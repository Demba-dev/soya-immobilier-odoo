from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class SoyaVisit(models.Model):
    _name = 'soya.visit'
    _description = 'Visite Immobilière'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'visit_date desc'

    # === CHAMPS PRINCIPAUX ===
    name = fields.Char(string="Référence Visite", readonly=True, copy=False, compute='_compute_name', store=True)
    
    visit_date = fields.Datetime(
        string="Date et Heure de la Visite",
        required=True,
        tracking=True
    )
    
    # Liens Principaux
    prospect_id = fields.Many2one(
        'soya.prospect',
        string='Prospect',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    property_id = fields.Many2one(
        'soya.property',
        string='Bien Immobilier',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    offer_id = fields.Many2one(
        'soya.property.offer',
        string='Offre Associée',
        ondelete='set null',
        tracking=True,
        help="Offre liée à cette visite si applicable"
    )
    
    # Agent immobilier
    salesperson_id = fields.Many2one(
        'res.users',
        string='Agent Immobilier',
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )
    
    # === STATUT ET SUIVI ===
    state = fields.Selection([
        ('planned', 'Planifiée'),
        ('in_progress', 'En Cours'),
        ('completed', 'Complétée'),
        ('cancelled', 'Annulée'),
        ('no_show', 'Non-Présentation'),
    ], string='Statut', default='planned', copy=False, tracking=True)
    
    # === FEEDBACK ET NOTES ===
    prospect_interest = fields.Selection([
        ('very_interested', 'Très Intéressé'),
        ('interested', 'Intéressé'),
        ('neutral', 'Neutre'),
        ('not_interested', 'Pas Intéressé'),
    ], string="Intérêt du Prospect", tracking=True)
    
    feedback = fields.Text(string="Commentaires de la Visite", tracking=True)
    
    visit_duration = fields.Float(
        string="Durée (minutes)",
        help="Durée estimée ou réelle de la visite en minutes"
    )
    
    # === SUIVI DE CONVERSION ===
    visit_date_end = fields.Datetime(string="Fin de la Visite")
    
    follow_up_date = fields.Date(
        string="Date de Suivi Prévue",
        tracking=True,
        help="Date prévue pour le suivi après la visite"
    )
    
    follow_up_done = fields.Boolean(
        string="Suivi Effectué",
        default=False,
        tracking=True
    )
    
    # Résultat
    converted_to_offer = fields.Boolean(
        string="Convertie en Offre",
        default=False,
        tracking=True,
        help="Cochez si cette visite a conduit à une offre"
    )
    
    created_offer_id = fields.Many2one(
        'soya.property.offer',
        string='Offre Créée',
        readonly=True,
        help="Offre créée suite à cette visite"
    )
    
    # === CHAMPS DE QUALITÉ ===
    quality_score = fields.Integer(
        string="Score de Qualité",
        default=0,
        help="De 0 à 10"
    )
    
    issues_found = fields.Text(
        string="Problèmes Identifiés",
        help="Problèmes ou points à améliorer du bien"
    )

    next_action_date = fields.Date(
        string="Date de Prochaine Action",
        tracking=True,
        help="Date prévue pour la prochaine action après la visite"
    )

    next_action = fields.Text(string="Prochaine Action")

    
    # === CHAMPS CALCULÉS ===
    @api.depends('prospect_id', 'property_id', 'visit_date')
    def _compute_name(self):
        for visit in self:
            if visit.prospect_id and visit.property_id:
                date_str = visit.visit_date.strftime('%d/%m/%Y') if visit.visit_date else 'Sans date'
                visit.name = f"{visit.prospect_id.name} - {visit.property_id.name} ({date_str})"
            else:
                visit.name = "Nouvelle Visite"
    
    # === CONTRAINTES ===
    @api.constrains('quality_score')
    def _check_quality_score(self):
        for visit in self:
            if visit.quality_score and (visit.quality_score < 0 or visit.quality_score > 10):
                raise ValidationError("Le score de qualité doit être entre 0 et 10")

    # === ACTIONS ===
    def action_mark_in_progress(self):
        self.write({
            'state': 'in_progress',
        })
    
    def action_mark_completed(self):
        self.write({
            'state': 'completed',
            'visit_date_end': datetime.now(),
        })
    
    def action_mark_no_show(self):
        self.write({'state': 'no_show'})
    
    def action_cancel_visit(self):
        self.write({'state': 'cancelled'})
    
    def action_create_offer(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Créer une Offre',
            'res_model': 'soya.visit.create.offer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_visit_id': self.id},
        }
    
    def action_mark_follow_up_done(self):
        self.write({'follow_up_done': True})

    def action_view_property(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bien Immobilier',
            'res_model': 'soya.property',
            'view_mode': 'form',
            'res_id': self.property_id.id,
            'target': 'new',
        }
    
    def action_view_prospect(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Prospect',
            'res_model': 'soya.prospect',
            'view_mode': 'form',
            'res_id': self.prospect_id.id,
            'target': 'new',
        }
