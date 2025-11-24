from odoo import models, fields, api


class SoyaPortalTicket(models.Model):
    _name = 'soya.portal.ticket'
    _description = 'Ticket de Support Client'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string="Référence", readonly=True, copy=False)
    subject = fields.Char(string="Sujet", required=True, tracking=True)
    description = fields.Text(string="Description", required=True)
    
    partner_id = fields.Many2one(
        'res.partner',
        string="Client",
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    property_id = fields.Many2one(
        'soya.property',
        string="Bien Immobilier (Optionnel)"
    )
    
    contract_id = fields.Many2one(
        'soya.rental.contract',
        string="Contrat (Optionnel)"
    )
    
    state = fields.Selection([
        ('open', 'Ouvert'),
        ('in_progress', 'En Cours'),
        ('resolved', 'Résolu'),
        ('closed', 'Fermé'),
    ], string="État", default='open', tracking=True)
    
    category = fields.Selection([
        ('technical', 'Problème Technique'),
        ('billing', 'Facturation'),
        ('maintenance', 'Maintenance'),
        ('general', 'Question Générale'),
        ('complaint', 'Réclamation'),
    ], string="Catégorie", required=True, default='general', tracking=True)
    
    priority = fields.Selection([
        ('low', 'Basse'),
        ('normal', 'Normal'),
        ('high', 'Haute'),
        ('urgent', 'Urgent'),
    ], string="Priorité", default='normal', tracking=True)
    
    assigned_to = fields.Many2one(
        'res.users',
        string="Assigné à",
        tracking=True
    )
    
    create_date = fields.Datetime(string="Créé le", readonly=True)
    write_date = fields.Datetime(string="Modifié le", readonly=True)
    resolution_date = fields.Datetime(string="Date Résolution")

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('soya.portal.ticket') or 'TICKET'
        return super().create(vals)

    def action_mark_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_mark_resolved(self):
        from datetime import datetime
        self.write({
            'state': 'resolved',
            'resolution_date': datetime.now()
        })

    def action_mark_closed(self):
        self.write({'state': 'closed'})

    def action_reopen(self):
        self.write({'state': 'open'})
