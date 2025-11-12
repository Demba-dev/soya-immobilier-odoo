from odoo import models, fields, api
from datetime import timedelta

class SoyaPayment(models.Model):
    _name = 'soya.payment'
    _description = 'Paiement Immobilier'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'payment_date desc'

    name = fields.Char(
        string='Numéro de Paiement',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self._generate_payment_number()
     
    )

    invoice_id = fields.Many2one(
        'soya.financial.invoice',
        string='Facture',
        required=True,
        ondelete='cascade'
        
    )

    partner_id = fields.Many2one(
        'res.partner',
        related='invoice_id.partner_id',
        string='Client',
        store=True,
        readonly=True
    )

    property_id = fields.Many2one(
        'soya.property',
        related='invoice_id.property_id',
        string='Propriété',
        store=True,
        readonly=True
    )

    amount = fields.Monetary(
        string='Montant Payé',
        required=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        required=True,
        default=lambda self: self.env.company.currency_id
    )

    payment_date = fields.Date(
        string='Date de Paiement',
        required=True,
        default=fields.Date.context_today
    )

    payment_method = fields.Selection([
        ('cash', 'Espèces'),
        ('check', 'Chèque'),
        ('bank_transfer', 'Virement Bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('other', 'Autre')
    ], string='Méthode de Paiement', required=True, default='bank_transfer')

    reference_number = fields.Char(
        string='Numéro de Référence',
        help='Numéro de chèque, de transfert, etc.'
    )

    notes = fields.Text(string='Notes')

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('reconciled', 'Réconcilié'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft')

    remaining_amount = fields.Monetary(
        string='Montant Restant',
        compute='_compute_remaining_amount',
        store=True,
        readonly=True
    )

    invoice_id = fields.Many2one(
        'soya.financial.invoice',
        string='Facture Associée',
        required=True,
        ondelete='cascade'
    )

    @api.depends('invoice_id.total_amount', 'invoice_id.payment_ids.amount')
    def _compute_remaining_amount(self):
        for payment in self:
            if payment.invoice_id:
                total_paid = sum(payment.invoice_id.payment_ids.mapped('amount'))
                payment.remaining_amount = payment.invoice_id.total_amount - total_paid
            else:
                payment.remaining_amount = 0

    def _generate_payment_number(self):
        return self.env['ir.sequence'].next_by_code('soya.payment') or 'PAY/000001'

    def action_confirm(self):
        self.state = 'confirmed'
        return True

    def action_reconcile(self):
        self.state = 'reconciled'
        return True

    def action_cancel(self):
        self.state = 'cancelled'
        return True

    def action_draft(self):
        self.state = 'draft'
        return True
    
    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Facture',
            'res_model': 'soya.financial.invoice',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
           
        }
