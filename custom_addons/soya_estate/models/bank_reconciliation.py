from odoo import models, fields, api

class SoyaBankReconciliation(models.Model):
    _name = 'soya.bank.reconciliation'
    _description = 'Réconciliation Bancaire'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'reconciliation_date desc'

    name = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('soya.bank.reconciliation') or 'RECON/000001',
        tracking=True
    )

    reconciliation_date = fields.Date(
        string='Date de Rapprochement',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )

    bank_statement_date = fields.Date(
        string='Date du Relevé Bancaire',
        required=True,
        tracking=True
    )

    bank_balance = fields.Monetary(
        string='Solde Bancaire',
        required=True,
        tracking=True
    )

    book_balance = fields.Monetary(
        string='Solde Comptable',
        compute='_compute_book_balance',
        store=True,
        readonly=True
    )

    difference = fields.Monetary(
        string='Différence',
        compute='_compute_difference',
        store=True,
        readonly=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        required=True,
        default=lambda self: self.env.company.currency_id
    )

    payment_ids = fields.Many2many(
        'soya.payment',
        string='Paiements Rapprochés',
        help='Sélectionnez les paiements correspondant au relevé bancaire'
    )

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('reconciled', 'Rapproché'),
        ('validated', 'Validé'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)

    notes = fields.Text(string='Notes')

    @api.depends('payment_ids.amount')
    def _compute_book_balance(self):
        for rec in self:
            rec.book_balance = sum(rec.payment_ids.mapped('amount'))

    @api.depends('bank_balance', 'book_balance')
    def _compute_difference(self):
        for rec in self:
            rec.difference = rec.bank_balance - rec.book_balance

    def action_reconcile(self):
        self.state = 'reconciled'
        for payment in self.payment_ids:
            if payment.state == 'confirmed':
                payment.action_reconcile()

    def action_validate(self):
        if self.difference != 0:
            raise ValueError('Le rapprochement doit être équilibré!')
        self.state = 'validated'

    def action_cancel(self):
        self.state = 'cancelled'
