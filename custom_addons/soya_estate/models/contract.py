from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class SoyaBaseContract(models.Model):
    _name = 'soya.base.contract'
    _description = 'Contrat Immobilier Base - SOYA'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    # === CHAMPS COMMUNS À TOUS LES CONTRATS ===
    name = fields.Char(
        string='Référence Contrat',
        required=True,
        default=lambda self: self._generate_contract_code(),
        tracking=True
    )

    
    # === BIEN IMMOBILIER ===
    property_id = fields.Many2one(
        'soya.property',
        string='Bien Immobilier',
        required=True,
        tracking=True
    )
    
    property_type_id = fields.Many2one(
        'soya.property.type',
        related='property_id.property_type_id',
        string='Type de Bien',
        readonly=True,
        store=True
    )
    
    # === PROPRIÉTAIRE ===
    landlord_id = fields.Many2one(
        'res.partner',
        string='Propriétaire',
        required=True,
        tracking=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
        tracking=True
    )
    
    # === DATES COMMUNES ===
    start_date = fields.Date(
        string='Date de Début',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    
    end_date = fields.Date(
        string='Date de Fin',
        tracking=True
    )
    
    # === ÉTAT DU CONTRAT ===
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('waiting_signature', 'En Attente Signature'),
        ('active', 'Actif'),
        ('expired', 'Expiré'),
        ('terminated', 'Résilié'),
        ('cancelled', 'Annulé'),
    ], string='État', default='draft', tracking=True)
    
    # === INFORMATIONS LÉGALES MALI ===
    land_title_reference = fields.Char(
        string='Référence Titre Foncier',
        related='property_id.land_title_number',
        readonly=True
    )
    
    court_jurisdiction = fields.Char(
        string='Tribunal Compétent',
        default='Tribunal de Commune IV, Bamako',
        help="Tribunal compétent en cas de litige"
    )
    
    # === DOCUMENTS ===
    document_ids = fields.One2many(
        'soya.contract.document',
        'contract_id',
        string='Documents Associés'
    )
    
    # === COMPTEURS ===
    remaining_days = fields.Integer(
        string='Jours Restants',
        compute='_compute_remaining_days'
    )
    
    is_expiring_soon = fields.Boolean(
        string='Expire Bientôt',
        compute='_compute_is_expiring_soon',
        store=True
    )
    
    # === CHAMPS CALCULÉS ===
    @api.depends('end_date')
    def _compute_remaining_days(self):
        """Calcul du nombre de jours restants avant expiration"""
        today = fields.Date.today()
        for contract in self:
            if contract.end_date and contract.state == 'active':
                end_date = fields.Date.from_string(contract.end_date)
                contract.remaining_days = (end_date - today).days
            else:
                contract.remaining_days = 0
    
    @api.depends('remaining_days')
    def _compute_is_expiring_soon(self):
        """Détermine si le contrat expire bientôt (moins de 30 jours)"""
        for contract in self:
            contract.is_expiring_soon = (
                contract.state == 'active' and 
                0 < contract.remaining_days <= 30
            )
    
    # === MÉTHODES COMMUNES ===
    def _generate_contract_code(self):
        """Générer un code unique pour le contrat"""
        return self.env['ir.sequence'].next_by_code('soya.base.contract.sequence') or 'Nouveau Contrat'
    
    def action_activate_contract(self):
        """Activer le contrat - À surcharger dans les modèles enfants"""
        for contract in self:
            if contract.state == 'waiting_signature':
                contract.state = 'active'
    
    def action_terminate_contract(self):
        """Résilier le contrat - À surcharger dans les modèles enfants"""
        for contract in self:
            if contract.state == 'active':
                contract.state = 'terminated'

    def action_generate_document(self):
        """Fonction temporaire - à compléter plus tard"""
        for contract in self:
            # Pour l'instant, juste changer l'état
            if contract.state == 'draft':
                contract.state = 'waiting_signature'
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'soya.base.contract',
                'view_mode': 'form',
                'res_id': contract.id,
                'target': 'current',
            }