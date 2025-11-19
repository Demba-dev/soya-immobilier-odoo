from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SoyaProspect(models.Model):
    _name = 'soya.prospect'
    _description = 'Prospect Immobilier'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # === CHAMPS PRINCIPAUX ===
    name = fields.Char(string="Nom du Prospect", required=True, tracking=True)
    phone = fields.Char(string="Téléphone", tracking=True)
    email = fields.Char(string="Email", tracking=True)
    
    # Adresse
    street = fields.Char(string="Rue")
    city = fields.Char(string="Ville")
    zip_code = fields.Char(string="Code Postal")
    country_id = fields.Many2one('res.country', string="Pays")
    
    # Informations Commerciales
    prospect_type = fields.Selection([
        ('buyer', 'Acheteur'),
        ('renter', 'Locataire'),
        ('investor', 'Investisseur'),
        ('other', 'Autre'),
    ], string="Type de Prospect", required=True, default='buyer', tracking=True)
    
    budget_min = fields.Float(string="Budget Minimum", tracking=True)
    budget_max = fields.Float(string="Budget Maximum", tracking=True)
    
    # Liens
    salesperson_id = fields.Many2one(
        'res.users',
        string='Agent Responsable',
        default=lambda self: self.env.user,
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Contact Associé',
        tracking=True,
        help="Contact res.partner optionnel pour intégration CRM"
    )
    
    # Statut
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('contacted', 'Contacté'),
        ('qualified', 'Qualifié'),
        ('visiting', 'En Visite'),
        ('converted', 'Converti'),
        ('lost', 'Perdu'),
        ('inactive', 'Inactif'),
    ], string='Statut', default='new', copy=False, tracking=True)
    
    # Visites associées
    visit_ids = fields.One2many(
        'soya.visit',
        'prospect_id',
        string='Visites'
    )
    
    visit_count = fields.Integer(string="Nombre de Visites", compute='_compute_visit_count', store=True)
    
    # Notes et Suivi
    notes = fields.Text(string="Notes")
    loss_reason = fields.Text(string="Raison de la Perte", help="À remplir si le prospect est perdu")
    
    # Dates
    first_contact_date = fields.Date(string="Date du Premier Contact", tracking=True)
    last_contact_date = fields.Date(string="Date du Dernier Contact", compute='_compute_last_contact')
    
    # === CHAMPS CALCULÉS ===
    @api.depends('visit_ids')
    def _compute_visit_count(self):
        for prospect in self:
            prospect.visit_count = len(prospect.visit_ids)
    
    @api.depends('visit_ids.visit_date')
    def _compute_last_contact(self):
        for prospect in self:
            if prospect.visit_ids:
                dates = prospect.visit_ids.mapped('visit_date')
                prospect.last_contact_date = max(dates) if dates else None
            else:
                prospect.last_contact_date = prospect.first_contact_date

    # === CONTRAINTES ===
    @api.constrains('budget_min', 'budget_max')
    def _check_budget(self):
        for prospect in self:
            if prospect.budget_min and prospect.budget_max:
                if prospect.budget_min > prospect.budget_max:
                    raise ValidationError("Le budget minimum ne peut pas être supérieur au budget maximum")

    # === ACTIONS ===
    def action_mark_contacted(self):
        self.write({'state': 'contacted'})

    def action_mark_qualified(self):
        self.write({'state': 'qualified'})

    def action_mark_converted(self):
        self.write({'state': 'converted'})

    def action_mark_lost(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Marquer comme Perdu',
            'res_model': 'soya.prospect.lost.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_prospect_id': self.id},
        }
    
    def action_view_visits(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Visites',
            'res_model': 'soya.visit',
            'view_mode': 'tree,form',
            'domain': [('prospect_id', '=', self.id)],
            'context': {'default_prospect_id': self.id},
        }
