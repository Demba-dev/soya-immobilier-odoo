from odoo import models, fields, api

class SoyaContractAmendment(models.Model):
    _name = 'soya.contract.amendment'
    _description = 'Avenant au Contrat - SOYA'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # === CONTRAT PARENT ===
    contract_id = fields.Many2one(
        'soya.base.contract',
        string='Contrat Parent',
        required=True,
        domain="[('state', '=', 'active')]",
        tracking=True
    )
    
    contract_type = fields.Selection([
        ('rental', 'Contrat de Location'),
        ('sale', 'Contrat de Vente'),
    ], string='Type de Contrat', compute='_compute_contract_type', store=True, readonly=True)
    
    # === TYPE D'AVENANT ===
    amendment_type = fields.Selection([
        ('rent_increase', 'Augmentation de Loyer'),
        ('duration_extension', 'Prolongation de Durée'),
        ('tenant_change', 'Changement de Locataire'),
        ('rent_decrease', 'Réduction de Loyer'),
        ('other', 'Autre Modification'),
    ], string='Type d\'Avenant', required=True, tracking=True)
    
    # === DATES ===
    amendment_date = fields.Date(
        string='Date de l\'Avenant',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    
    effective_date = fields.Date(
        string='Date d\'Effet',
        required=True,
        tracking=True
    )
    
    # === MODIFICATIONS ===
    description = fields.Text(
        string='Description des Modifications',
        required=True,
        tracking=True
    )
    
    old_value = fields.Char(
        string='Ancienne Valeur',
        tracking=True
    )
    
    new_value = fields.Char(
        string='Nouvelle Valeur',
        tracking=True
    )
    
    # === ÉTAT ===
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('signed', 'Signé'),
        ('cancelled', 'Annulé'),
    ], string='État', default='draft', tracking=True)
    
    # === MÉTHODES ===
    def action_validate_amendment(self):
        """Valider et appliquer l'avenant"""
        for amendment in self:
            if amendment.state == 'draft':
                amendment.state = 'signed'
                # TODO: Appliquer les modifications au contrat parent
    
    def _get_contract_reference(self):
        """Générer la référence de l'avenant"""
        if self.contract_id:
            return f"AVENANT-{self.contract_id.name}"
        return "AVENANT-NOUVEAU"

    # Ajouter cette méthode
    @api.depends('contract_id')
    def _compute_contract_type(self):
        """Détermine le type de contrat basé sur le modèle lié"""
        model_mapping = {
            'soya.rental.contract': 'rental',
            'soya.sale.contract': 'sale'
        }
        for amendment in self:
            if amendment.contract_id:
                amendment.contract_type = model_mapping.get(amendment.contract_id._name, False)
            else:
                amendment.contract_type = False