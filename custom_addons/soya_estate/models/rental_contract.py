from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta

class SoyaRentalContract(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _name = 'soya.rental.contract'
    _description = 'Contrat de Location - SOYA'
    _inherits = {'soya.base.contract': 'base_contract_id'}


    base_contract_id = fields.Many2one(
        'soya.base.contract',
        string='Contrat de Base',
        required=True,
        ondelete='cascade'
    )
    
    # === CHAMPS SPÉCIFIQUES LOCATION ===
    tenant_id = fields.Many2one(
        'res.partner',
        string='Locataire',
        required=True,
        domain="[('type', '=', 'contact')]",
        tracking=True
    )
    
    # === CONDITIONS FINANCIÈRES LOCATION ===
    # Explicitly define currency_id here to ensure it's recognized by monthly_rent
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
        tracking=True
    )

    monthly_rent = fields.Monetary(
        string='Loyer Mensuel (FCFA)',
        currency_field='currency_id',
        required=True,
        tracking=True
    )
    
    deposit_amount = fields.Monetary(
        string='Dépôt de Garantie (FCFA)',
        currency_field='currency_id',
        help="Dépôt de garantie (2 mois maximum selon loi malienne)",
        tracking=True
    )
    
    charges_amount = fields.Monetary(
        string='Charges Mensuelles (FCFA)',
        currency_field='currency_id',
        help="Charges récupérables (eau, électricité, entretien)",
        tracking=True
    )
    
    # === DURÉE LOCATION ===
    duration_months = fields.Integer(
        string='Durée (mois)',
        default=12,
        required=True,
        tracking=True
    )
    
    renewal_conditions = fields.Selection([
        ('tacit', 'Reconduction Tacite'),
        ('explicit', 'Reconduction Explicite'),
        ('none', 'Pas de Reconduction'),
    ], string='Conditions de Renouvellement', default='tacit', tracking=True)
    
    notice_period = fields.Integer(
        string='Délai de Préavis (jours)',
        default=30,
        help="Délai de préavis pour résiliation (jours)"
    )

    def action_generate_document(self):
        for contract in self:
            if contract.base_contract_id:
                return contract.base_contract_id.action_generate_document()
    
    # === CALCUL AUTOMATIQUE DATE FIN ===
    @api.depends('start_date', 'duration_months')
    def _compute_end_date(self):
        """Calcul automatique de la date de fin basée sur la durée"""
        for contract in self:
            if contract.start_date and contract.duration_months:
                start_date = fields.Date.from_string(contract.start_date)
                end_date = start_date + timedelta(days=contract.duration_months * 30)
                contract.end_date = fields.Date.to_string(end_date)
            else:
                contract.end_date = False
    
    # === CONTRAINTES SPÉCIFIQUES LOCATION ===
    @api.constrains('deposit_amount', 'monthly_rent')
    def _check_deposit_amount(self):
        """Vérifie que le dépôt de garantie ne dépasse pas 2 mois de loyer (loi malienne)"""
        for contract in self:
            if contract.deposit_amount > 0:
                max_deposit = contract.monthly_rent * 2
                if contract.deposit_amount > max_deposit:
                    raise ValidationError(
                        f"Le dépôt de garantie ne peut pas dépasser 2 mois de loyer "
                        f"({max_deposit:,.0f} FCFA) selon la loi malienne."
                    )
    
    @api.constrains('duration_months')
    def _check_duration(self):
        """Vérifie la durée du contrat de location"""
        for contract in self:
            if contract.duration_months < 1:
                raise ValidationError("La durée du contrat doit être d'au moins 1 mois")
    
    # === ACTIONS SPÉCIFIQUES LOCATION ===
    def action_activate_contract(self):
        """Activer le contrat de location"""
        for contract in self:
            if contract.state == 'waiting_signature':
                contract.state = 'active'
                # Mettre à jour le statut du bien
                if contract.property_id:
                    contract.property_id.state = 'rented'
                    contract.property_id.current_tenant_id = contract.tenant_id
    
    def action_terminate_contract(self):
        """Résilier le contrat de location"""
        for contract in self:
            if contract.state == 'active':
                contract.state = 'terminated'
                # Remettre le bien disponible
                if contract.property_id:
                    contract.property_id.state = 'new'
                    contract.property_id.current_tenant_id = False

    def _valid_field_parameter(self, field, param):
        return param == 'tracking' or super()._valid_field_parameter(field, param)
