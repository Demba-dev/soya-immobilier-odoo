from odoo import models, fields, api

class SoyaPaymentHistory(models.Model):
    _name = 'soya.payment.history'
    _description = 'Historique des Transactions'
    _order = 'transaction_date desc'
    _auto = False

    payment_id = fields.Many2one('soya.payment', string='Paiement', readonly=True)
    transaction_date = fields.Date(string='Date Transaction', readonly=True)
    transaction_time = fields.Char(string='Heure', readonly=True)
    
    invoice_id = fields.Many2one('soya.financial.invoice', string='Facture', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Client', readonly=True)
    property_id = fields.Many2one('soya.property', string='Propriété', readonly=True)
    
    amount = fields.Monetary(string='Montant', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Devise', readonly=True)
    
    payment_method = fields.Selection([
        ('cash', 'Espèces'),
        ('check', 'Chèque'),
        ('bank_transfer', 'Virement Bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('other', 'Autre')
    ], string='Méthode', readonly=True)
    
    reference_number = fields.Char(string='Référence', readonly=True)
    status = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('reconciled', 'Réconcilié'),
        ('cancelled', 'Annulé')
    ], string='Statut', readonly=True)
    
    user_id = fields.Many2one('res.users', string='Utilisateur', readonly=True)

    def init(self):
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW soya_payment_history AS (
                SELECT
                    row_number() OVER () as id,
                    sp.id as payment_id,
                    sp.payment_date as transaction_date,
                    EXTRACT(HOUR FROM sp.create_date)::text || ':' || 
                    LPAD(EXTRACT(MINUTE FROM sp.create_date)::text, 2, '0') as transaction_time,
                    sp.invoice_id,
                    sp.partner_id,
                    sp.property_id,
                    sp.amount,
                    sp.currency_id,
                    sp.payment_method,
                    sp.reference_number,
                    sp.state as status,
                    sp.write_uid as user_id
                FROM soya_payment sp
                ORDER BY sp.payment_date DESC
            )
        ''')
