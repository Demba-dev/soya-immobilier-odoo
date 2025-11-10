import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
from datetime import date, timedelta

class SoyaPropertyOffer(models.Model):
    _name = 'soya.property.offer'
    _description = 'Offre Immobilière'
    _order = 'price desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # === CHAMPS EXISTANTS (CONSERVÉS) ===
    price = fields.Float(string="Prix Proposé", required=True, tracking=True)
    status = fields.Selection(
        [('accepted', 'Acceptée'), ('refused', 'Refusée')],
        string='Statut',
        copy=False,
        tracking=True
    )
    
    # Liaison Many2one vers le Bien Immobilier
    property_id = fields.Many2one(
        'soya.property',
        string='Bien Associé',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Acheteur/Partenaire',
        required=True,
        tracking=True
    )
    
    date_deadline = fields.Date(string="Date Limite", tracking=True)
    
    # === NOUVEAUX CHAMPS - TYPES D'OFFRE ===
    offer_type = fields.Selection([
        ('purchase', 'Offre d\'achat'),
        ('rental', 'Offre de location'),
        ('reservation', 'Réservation'),
        ('partnership', 'Offre de partenariat')
    ], string="Type d'offre", required=True, default='purchase', tracking=True)
    
    # === INFORMATIONS COMPLÈMENTAIRES ===
    name = fields.Char(
        string="Référence offre",
        default=lambda self: self._generate_offer_code(),
        readonly=True
    )
    
    offer_date = fields.Datetime(
        string="Date de l'offre",
        default=fields.Datetime.now,
        readonly=True
    )
    
    validity_days = fields.Integer(
        string="Validité (jours)",
        default=7,
        required=True,
        tracking=True
    )
    
    # === CONDITIONS FINANCIÈRES ===
    proposed_deposit = fields.Float(
        string="Dépôt proposé (FCFA)",
        help="Dépôt de garantie ou acompte proposé"
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string="Devise",
        default=lambda self: self.env.ref('base.XOF'),
        readonly=True
    )
    
    payment_terms = fields.Selection([
        ('cash', 'Comptant'),
        ('installment_3', '3 échéances'),
        ('installment_6', '6 échéances'),
        ('installment_12', '12 échéances'),
        ('bank_loan', 'Prêt bancaire'),
        ('mixed', 'Mixte')
    ], string="Modalités de paiement", default='cash', tracking=True)
    
    # === POUR LES OFFRES DE LOCATION ===
    rental_duration = fields.Integer(
        string="Durée location (mois)",
        default=12,
        help="Durée proposée pour la location"
    )
    
    proposed_start_date = fields.Date(
        string="Date début souhaitée"
    )
    
    proposed_end_date = fields.Date(
        string="Date fin souhaitée",
        compute='_compute_proposed_end_date'
    )
    
    # === STATUT ÉTENDU ===
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumise'),
        ('accepted', 'Acceptée'),
        ('refused', 'Refusée'),
        ('expired', 'Expirée'),
        ('cancelled', 'Annulée')
    ], string="État", default='draft', tracking=True)
    
    # === SUIVI COMMERCIAL ===
    salesperson_id = fields.Many2one(
        'res.users',
        string="Commercial responsable",
        default=lambda self: self.env.user,
        tracking=True
    )
    
    commission_rate = fields.Float(
        string="Taux commission (%)",
        compute='_compute_commission_rate'
    )
    
    commission_amount = fields.Float(
        string="Montant commission (FCFA)",
        compute='_compute_commission_amount'
    )
    
    # === INFORMATIONS DE SUIVI ===
    next_followup_date = fields.Date(
        string="Prochaine relance"
    )
    
    followup_notes = fields.Text(
        string="Notes de suivi"
    )
    
    refusal_reason = fields.Text(
        string="Raison du refus"
    )
    
    acceptance_date = fields.Datetime(
        string="Date d'acceptation"
    )
    
    accepted_by = fields.Many2one(
        'res.users',
        string="Accepté par"
    )
    
    special_conditions = fields.Text(
        string="Conditions Spéciales",
        help="Conditions particulières proposées par le client"
    )
    
    # === CHAMPS CALCULÉS ===
    expiry_date = fields.Date(
        string="Date d'expiration",
        compute='_compute_expiry_date',
        store=True,
        search=True
    )
    
    is_expired = fields.Boolean(
        string="Expirée",
        compute='_compute_is_expired'
    )
    
    days_until_expiry = fields.Integer(
        string="Jours avant expiration",
        compute='_compute_days_until_expiry'
    )
    
    # === RELATIONS ===
    contract_id = fields.Many2one(
        'soya.property.contract',
        string="Contrat généré"
    )
    
    # === CHAMPS CALCULÉS - IMPLÉMENTATION ===
    @api.depends('proposed_start_date', 'rental_duration')
    def _compute_proposed_end_date(self):
        """Calcul de la date de fin basée sur la durée de location"""
        for record in self:
            if record.proposed_start_date and record.rental_duration:
                start_date = fields.Date.from_string(record.proposed_start_date)
                end_date = start_date + timedelta(days=record.rental_duration * 30)
                record.proposed_end_date = fields.Date.to_string(end_date)
            else:
                record.proposed_end_date = False
    
    @api.depends('offer_date', 'validity_days')
    def _compute_expiry_date(self):
        """Calcul de la date d'expiration"""
        for record in self:
            if record.offer_date and record.validity_days:
                offer_datetime = fields.Datetime.from_string(record.offer_date)
                expiry_datetime = offer_datetime + timedelta(days=record.validity_days)
                record.expiry_date = fields.Datetime.to_string(expiry_datetime).split()[0]
            else:
                record.expiry_date = False
    
    @api.depends('expiry_date')
    def _compute_is_expired(self):
        """Vérifier si l'offre est expirée"""
        today = date.today()
        for record in self:
            if record.expiry_date:
                record.is_expired = fields.Date.from_string(record.expiry_date) < today
            else:
                record.is_expired = False
    
    @api.depends('expiry_date')
    def _compute_days_until_expiry(self):
        """Calcul du nombre de jours avant expiration"""
        today = date.today()
        for record in self:
            if record.expiry_date:
                expiry_date = fields.Date.from_string(record.expiry_date)
                record.days_until_expiry = (expiry_date - today).days
            else:
                record.days_until_expiry = 0
    
    @api.depends('property_id.property_type_id')
    def _compute_commission_rate(self):
        """Calcul du taux de commission basé sur le type de bien"""
        for record in self:
            if record.property_id and record.property_id.property_type_id:
                if record.offer_type == 'purchase':
                    record.commission_rate = record.property_id.property_type_id.sales_commission_rate
                elif record.offer_type == 'rental':
                    record.commission_rate = record.property_id.property_type_id.rental_commission_rate
                else:
                    record.commission_rate = 0.0
            else:
                record.commission_rate = 0.0
    
    @api.depends('price', 'commission_rate')
    def _compute_commission_amount(self):
        """Calcul du montant de commission"""
        for record in self:
            record.commission_amount = (record.price * record.commission_rate) / 100
    
    # === CONTRAINTES ET VALIDATIONS ===
    @api.constrains('price')
    def _check_positive_price(self):
        """Vérifier que le prix est positif"""
        for record in self:
            if record.price <= 0:
                raise ValidationError("Le prix proposé doit être positif")
    
    @api.constrains('validity_days')
    def _check_validity_days(self):
        """Vérifier la validité en jours"""
        for record in self:
            if record.validity_days < 1:
                raise ValidationError("La validité doit être d'au moins 1 jour")
    
    @api.constrains('rental_duration')
    def _check_rental_duration(self):
        """Vérifier la durée de location"""
        for record in self:
            if record.offer_type == 'rental' and record.rental_duration < 1:
                raise ValidationError("La durée de location doit être d'au moins 1 mois")
    
    @api.constrains('property_id', 'partner_id', 'offer_type')
    def _check_unique_offer(self):
        """Éviter les doublons d'offres"""
        for record in self:
            if record.state in ['draft', 'submitted']:
                existing_offers = self.search([
                    ('property_id', '=', record.property_id.id),
                    ('partner_id', '=', record.partner_id.id),
                    ('offer_type', '=', record.offer_type),
                    ('state', 'in', ['draft', 'submitted']),
                    ('id', '!=', record.id)
                ])
                if existing_offers:
                    raise ValidationError(
                        "Une offre du même type existe déjà pour ce bien et ce partenaire"
                    )
    
    # === MÉTHODES D'ACTION ===
    def action_submit_offer(self):
        """Soumettre l'offre"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError("Seules les offres brouillons peuvent être soumises")
            
            # Vérifier qu'il n'y a pas d'autre offre acceptée
            accepted_offers = self.search([
                ('property_id', '=', record.property_id.id),
                ('state', '=', 'accepted')
            ])
            if accepted_offers:
                raise ValidationError(
                    "Une offre a déjà été acceptée pour ce bien. Vous ne pouvez pas soumettre une nouvelle offre."
                )
            
            record.state = 'submitted'
            
            # Mettre à jour le statut du bien
            if record.property_id.state == 'new':
                record.property_id.state = 'offer_received'
    
    def action_accept_offer(self):
        """Accepter l'offre"""
        for record in self:
            if record.state != 'submitted':
                raise ValidationError("Seules les offres soumises peuvent être acceptées")
            
            # Refuser automatiquement les autres offres
            other_offers = self.search([
                ('property_id', '=', record.property_id.id),
                ('state', '=', 'submitted'),
                ('id', '!=', record.id)
            ])
            other_offers.write({'state': 'refused', 'status': 'refused'})
            
            # Accepter cette offre
            record.state = 'accepted'
            record.status = 'accepted'
            record.acceptance_date = fields.Datetime.now()
            record.accepted_by = self.env.user
            
            # Mettre à jour le statut du bien
            record.property_id.state = 'offer_accepted'
            
            # Si c'est une offre d'achat, mettre à jour le prix de vente
            if record.offer_type == 'purchase':
                record.property_id.selling_price = record.price
    
    def action_refuse_offer(self):
        """Refuser l'offre"""
        for record in self:
            if record.state not in ['submitted', 'draft']:
                raise ValidationError("Seules les offres soumises ou brouillons peuvent être refusées")
            
            record.state = 'refused'
            record.status = 'refused'
            
            # Vérifier s'il reste des offres soumises pour le bien
            remaining_offers = self.search([
                ('property_id', '=', record.property_id.id),
                ('state', '=', 'submitted')
            ])
            if not remaining_offers:
                record.property_id.state = 'new'
    
    def action_cancel_offer(self):
        """Annuler l'offre"""
        for record in self:
            record.state = 'cancelled'
    
    def action_reset_to_draft(self):
        """Remettre l'offre en brouillon"""
        for record in self:
            if record.state in ['refused', 'cancelled', 'expired']:
                record.state = 'draft'
                record.status = False
                record.refusal_reason = False
    
    def action_schedule_followup(self):
        """Planifier une relance"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Planifier Relance',
            'res_model': 'soya.schedule.followup',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_offer_id': self.id}
        }
    
    # === MÉTHODES TECHNIQUES ===
    def _generate_offer_code(self):
        """Générer un code unique pour l'offre"""
        return self.env['ir.sequence'].next_by_code('soya.property.offer.sequence') or 'Nouvelle Offre'
    
    @api.model
    def create(self, vals):
        """Surcharge de la création"""
        if not vals.get('name') or vals.get('name') == 'Nouvelle Offre':
            vals['name'] = self._generate_offer_code()
        return super().create(vals)
    
    # === CRON JOB POUR LES OFFRES EXPIRÉES ===
    @api.model
    def _cron_check_expired_offers(self):
        """Vérifier et marquer les offres expirées (exécuté quotidiennement)"""
        expired_offers = self.search([
            ('state', '=', 'submitted'),
            ('is_expired', '=', True)
        ])
        expired_offers.write({'state': 'expired'})
        
        # Logger l'action
        _logger.info(f"{len(expired_offers)} offres marquées comme expirées")
