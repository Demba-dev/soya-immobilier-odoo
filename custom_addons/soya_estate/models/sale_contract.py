from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SoyaSaleContract(models.Model):
    _name = 'soya.sale.contract'
    _description = 'Contrat de Vente - SOYA'
    _inherit = 'soya.base.contract'
    
    # === CHAMPS SPÉCIFIQUES VENTE ===
    buyer_id = fields.Many2one(
        'res.partner',
        string='Acheteur',
        required=True,
        domain="[('type', '=', 'contact')]",
        tracking=True
    )
    
    # === CONDITIONS FINANCIÈRES VENTE ===
    sale_price = fields.Monetary(
        string='Prix de Vente (FCFA)',
        currency_field='currency_id',
        required=True,
        tracking=True
    )
    
    down_payment = fields.Monetary(
        string='Acompte (FCFA)',
        currency_field='currency_id',
        tracking=True
    )
    
    payment_terms = fields.Selection([
        ('cash', 'Comptant'),
        ('installment_3', '3 échéances'),
        ('installment_6', '6 échéances'),
        ('installment_12', '12 échéances'),
        ('bank_loan', 'Prêt bancaire'),
    ], string='Modalités de Paiement', default='cash', tracking=True)
    
    # === NOTAIRE ET ACTE ===
    notary_id = fields.Many2one(
        'res.partner',
        string='Notaire',
        domain="[('type', '=', 'contact')]",
        help="Notaire en charge de la transaction",
        tracking=True
    )
    
    deed_date = fields.Date(
        string="Date de l'Acte",
        tracking=True
    )
    
    deed_reference = fields.Char(
        string="Référence de l'Acte",
        tracking=True
    )
    
    # === CONDITIONS SUSPENSIVES ===
    suspensive_conditions = fields.Text(
        string='Conditions Suspensives',
        help="Conditions devant être remplies pour la vente (prêt bancaire, etc.)"
    )
    
    # === ACTIONS SPÉCIFIQUES VENTE ===
    def action_activate_contract(self):
        """Activer le contrat de vente"""
        for contract in self:
            if contract.state == 'waiting_signature':
                contract.state = 'active'
                # Mettre à jour le statut du bien
                if contract.property_id:
                    contract.property_id.state = 'sold'
                    contract.property_id.selling_price = contract.sale_price
    
    def action_terminate_contract(self):
        """Résilier le contrat de vente"""
        for contract in self:
            if contract.state == 'active':
                contract.state = 'terminated'
                # Remettre le bien disponible
                if contract.property_id:
                    contract.property_id.state = 'new'
                    contract.property_id.selling_price = 0.0