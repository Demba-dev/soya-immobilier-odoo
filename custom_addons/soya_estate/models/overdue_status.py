
from odoo import models, fields, api
from datetime import datetime, timedelta

class SoyaOverdueStatus(models.Model):
    _name = 'soya.overdue.status'
    _description = 'État des Impayés'
    _order = 'days_overdue desc'
    _auto = False
    _table = 'soya_overdue_status'

    invoice_id = fields.Many2one('soya.financial.invoice', string='Facture', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Client', readonly=True)
    property_id = fields.Many2one('soya.property', string='Propriété', readonly=True)
    
    invoice_number = fields.Char(string='Numéro Facture', readonly=True)
    total_amount = fields.Monetary(string='Montant Total', readonly=True)
    paid_amount = fields.Monetary(string='Montant Payé', readonly=True)
    remaining_amount = fields.Monetary(string='Montant Restant', readonly=True)
    
    currency_id = fields.Many2one('res.currency', string='Devise', readonly=True)
    
    due_date = fields.Date(string='Date Échéance', readonly=True)
    days_overdue = fields.Integer(string='Jours en Retard', readonly=True)
    
    invoice_state = fields.Selection([
        ('draft', 'Brouillon'),
        ('pending', 'En Attente'),
        ('paid', 'Payée'),
        ('partial', 'Partiellement Payée'),
        ('overdue', 'En Retard'),
    ], string='État Facture', readonly=True)

    def init(self):
        self.env.cr.execute('DROP VIEW IF EXISTS soya_overdue_status CASCADE')
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW soya_overdue_status AS (
                SELECT
                    row_number() OVER () as id,
                    fi.id as invoice_id,
                    fi.partner_id,
                    fi.property_id,
                    fi.name as invoice_number,
                    fi.total_amount,
                    COALESCE(SUM(sp.amount), 0) as paid_amount,
                    fi.total_amount - COALESCE(SUM(sp.amount), 0) as remaining_amount,
                    fi.currency_id,
                    fi.due_date,
                    CASE
                        WHEN fi.due_date IS NULL THEN 0
                        WHEN fi.due_date < CURRENT_DATE THEN (CURRENT_DATE - fi.due_date)
                        ELSE 0
                    END as days_overdue,
                    CASE
                        WHEN fi.state = 'draft' THEN 'draft'
                        WHEN fi.state = 'cancelled' THEN 'draft'
                        WHEN COALESCE(SUM(sp.amount), 0) = 0 THEN 
                            CASE WHEN fi.due_date < CURRENT_DATE THEN 'overdue' ELSE 'pending' END
                        WHEN COALESCE(SUM(sp.amount), 0) < fi.total_amount THEN 'partial'
                        ELSE 'paid'
                    END as invoice_state
                FROM soya_financial_invoice fi
                LEFT JOIN soya_payment sp ON fi.id = sp.invoice_id AND sp.state IN ('confirmed', 'reconciled')
                WHERE fi.state NOT IN ('draft', 'cancelled')
                GROUP BY fi.id, fi.partner_id, fi.property_id, fi.name, 
                         fi.total_amount, fi.currency_id, fi.due_date, fi.state
            )
        ''')