from odoo import models, fields, api
from datetime import date, timedelta


class SoyaSalesActivity(models.Model):
    _name = 'soya.sales.activity'
    _description = 'Activité Commerciale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'activity_date desc'

    # === CHAMPS PRINCIPAUX ===
    name = fields.Char(string="Description", required=True, tracking=True)
    
    activity_date = fields.Date(
        string="Date de l'Activité",
        required=True,
        default=lambda self: date.today(),
        tracking=True
    )
    
    # Liens
    salesperson_id = fields.Many2one(
        'res.users',
        string='Agent Responsable',
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )
    
    prospect_id = fields.Many2one(
        'soya.prospect',
        string='Prospect',
        ondelete='cascade',
        tracking=True
    )
    
    property_id = fields.Many2one(
        'soya.property',
        string='Bien Immobilier',
        ondelete='cascade',
        tracking=True
    )
    
    visit_id = fields.Many2one(
        'soya.visit',
        string='Visite Associée',
        ondelete='set null',
        tracking=True
    )
    
    # === TYPE D'ACTIVITÉ ===
    activity_type = fields.Selection([
        ('call', 'Appel Téléphonique'),
        ('meeting', 'Réunion'),
        ('email', 'Email'),
        ('visit', 'Visite'),
        ('quote', 'Devis'),
        ('proposal', 'Proposition'),
        ('follow_up', 'Suivi'),
        ('other', 'Autre'),
    ], string="Type d'Activité", required=True, tracking=True)
    
    # === DÉTAILS ===
    description = fields.Text(string="Description Détaillée")
    
    duration = fields.Float(
        string="Durée (minutes)",
        help="Durée estimée ou réelle de l'activité"
    )
    
    outcome = fields.Selection([
        ('positive', 'Positif'),
        ('neutral', 'Neutre'),
        ('negative', 'Négatif'),
        ('pending', 'En Attente'),
    ], string="Résultat", default='pending', tracking=True)
    
    # === SUIVI ===
    completed = fields.Boolean(
        string="Complétée",
        default=False,
        tracking=True
    )
    
    next_action = fields.Text(string="Prochaine Action")
    next_action_date = fields.Date(
        string="Date de la Prochaine Action",
        tracking=True
    )
    
    # === CHAMPS CALCULÉS ===
    days_since_activity = fields.Integer(
        string="Jours depuis l'Activité",
        compute='_compute_days_since_activity'
    )
    
    is_overdue = fields.Boolean(
        string="En Retard",
        compute='_compute_is_overdue'
    )
    
    @api.depends('activity_date')
    def _compute_days_since_activity(self):
        for activity in self:
            if activity.activity_date:
                activity.days_since_activity = (date.today() - activity.activity_date).days
            else:
                activity.days_since_activity = 0
    
    @api.depends('next_action_date')
    def _compute_is_overdue(self):
        today = date.today()
        for activity in self:
            if activity.next_action_date and activity.next_action_date < today:
                activity.is_overdue = True
            else:
                activity.is_overdue = False

    # === ACTIONS ===
    def action_mark_completed(self):
        self.write({'completed': True})
    
    def action_mark_pending(self):
        self.write({'completed': False})

    # === STATISTIQUES ===
    @staticmethod
    def get_activities_by_type(salesperson_id=None, start_date=None, end_date=None):
        domain = []
        if salesperson_id:
            domain.append(('salesperson_id', '=', salesperson_id))
        if start_date:
            domain.append(('activity_date', '>=', start_date))
        if end_date:
            domain.append(('activity_date', '<=', end_date))
        
        activities = models.Model.search(domain)
        result = {}
        for activity in activities:
            activity_type = activity.activity_type
            result[activity_type] = result.get(activity_type, 0) + 1
        return result
