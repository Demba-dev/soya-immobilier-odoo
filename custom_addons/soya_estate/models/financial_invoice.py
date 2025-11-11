from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class SoyaFinancialInvoice(models.Model):
    _name = 'soya.financial.invoice'
    _description = 'Facture Financière SOYA'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'invoice_date desc, id desc'
    
    # === INFORMATIONS GÉNÉRALES ===
    name = fields.Char(
        string='Référence Facture',
        required=True,
        default=lambda self: self._generate_invoice_number(),
        tracking=True
    )
    
    invoice_type = fields.Selection([
        ('rent', 'Quittance de Loyer'),
        ('charge', 'Facture de Charges'),
        ('commission', 'Facture de Commission'),
        ('penalty', 'Pénalité de Retard'),
        ('other', 'Autre Facture')
    ], string='Type de Facture', required=True, default='rent', tracking=True)
    
    # === RELATIONS ===
    contract_id = fields.Many2one(
        'soya.rental.contract',
        string='Contrat Lié',
        domain="[('state', '=', 'active')]",
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Client/Débiteur',
        required=True,
        tracking=True
    )
    
    property_id = fields.Many2one(
        'soya.property',
        string='Bien Immobilier',
        related='contract_id.property_id',
        store=True,
        readonly=True
    )
    
    # === INFORMATIONS FINANCIÈRES ===
    amount = fields.Monetary(
        string='Montant HT (FCFA)',
        required=True,
        tracking=True
    )
    
    tax_amount = fields.Monetary(
        string='Montant TVA (FCFA)',
        compute='_compute_tax_amount',
        store=True,
        tracking=True
    )
    
    total_amount = fields.Monetary(
        string='Montant TTC (FCFA)',
        compute='_compute_total_amount',
        store=True,
        tracking=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    
    # === PÉRIODE DE FACTURATION ===
    invoice_date = fields.Date(
        string='Date de Facturation',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    
    due_date = fields.Date(
        string='Date d\'Échéance',
        compute='_compute_due_date',
        store=True,
        tracking=True
    )
    
    period_start = fields.Date(
        string='Début de Période',
        required=True,
        tracking=True
    )
    
    period_end = fields.Date(
        string='Fin de Période',
        required=True,
        tracking=True
    )
    
    # === ÉTAT DE LA FACTURE ===
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoyée'),
        ('paid', 'Payée'),
        ('overdue', 'En Retard'),
        ('cancelled', 'Annulée')
    ], string='État', default='draft', tracking=True)
    
    payment_date = fields.Date(string='Date de Paiement', tracking=True)
    
    # === INFORMATIONS DE SUIVI ===
    is_overdue = fields.Boolean(
        string='En Retard',
        compute='_compute_is_overdue',
        store=True
    )
    
    overdue_days = fields.Integer(
        string='Jours de Retard',
        compute='_compute_overdue_days'
    )
    
    # === CHAMPS CALCULÉS ===
    @api.depends('amount', 'invoice_type')
    def _compute_tax_amount(self):
        """Calcul du montant de TVA (0% pour loyers résidentiels au Mali)"""
        for invoice in self:
            if invoice.invoice_type == 'rent':
                # Les loyers résidentiels sont exonérés de TVA au Mali
                invoice.tax_amount = 0.0
            else:
                # 18% de TVA pour les autres services
                invoice.tax_amount = invoice.amount * 0.18
    
    @api.depends('amount', 'tax_amount')
    def _compute_total_amount(self):
        """Calcul du montant total TTC"""
        for invoice in self:
            invoice.total_amount = invoice.amount + invoice.tax_amount
    
    @api.depends('invoice_date')
    def _compute_due_date(self):
        """Calcul de la date d'échéance (5 jours après facturation pour loyers)"""
        for invoice in self:
            if invoice.invoice_date:
                if invoice.invoice_type == 'rent':
                    invoice.due_date = invoice.invoice_date + timedelta(days=5)
                else:
                    invoice.due_date = invoice.invoice_date + timedelta(days=30)
    
    @api.depends('due_date', 'state')
    def _compute_is_overdue(self):
        """Détermine si la facture est en retard"""
        today = fields.Date.today()
        for invoice in self:
            invoice.is_overdue = (
                invoice.state == 'sent' and 
                invoice.due_date and 
                invoice.due_date < today
            )
    
    @api.depends('due_date')
    def _compute_overdue_days(self):
        """Calcule le nombre de jours de retard"""
        today = fields.Date.today()
        for invoice in self:
            if invoice.due_date and invoice.due_date < today and invoice.state == 'sent':
                invoice.overdue_days = (today - invoice.due_date).days
            else:
                invoice.overdue_days = 0
    
    # === CONTRAINTES ===
    @api.constrains('period_start', 'period_end')
    def _check_period_dates(self):
        """Vérifie que la période est valide"""
        for invoice in self:
            if invoice.period_start and invoice.period_end:
                if invoice.period_end <= invoice.period_start:
                    raise ValidationError("La date de fin de période doit être après la date de début.")
    
    @api.constrains('amount')
    def _check_positive_amount(self):
        """Vérifie que le montant est positif"""
        for invoice in self:
            if invoice.amount <= 0:
                raise ValidationError("Le montant de la facture doit être positif.")
    
    # === MÉTHODES D'ACTION ===
    def _generate_invoice_number(self):
        """Génération automatique du numéro de facture"""
        return self.env['ir.sequence'].next_by_code('soya.financial.invoice') or 'FAC-NEW'
    
    def action_validate_invoice(self):
        """Valider et envoyer la facture"""
        for invoice in self:
            if invoice.state == 'draft':
                invoice.state = 'sent'
                # TODO: Envoyer un email au client
    
    def action_mark_paid(self):
        """Marquer la facture comme payée"""
        for invoice in self:
            if invoice.state in ['sent', 'overdue']:
                invoice.state = 'paid'
                invoice.payment_date = fields.Date.today()
    
    def action_cancel_invoice(self):
        """Annuler la facture"""
        for invoice in self:
            if invoice.state != 'paid':
                invoice.state = 'cancelled'
    
    def action_generate_penalty(self):
        """Générer automatiquement une pénalité de retard"""
        for invoice in self:
            if invoice.invoice_type == 'rent' and invoice.is_overdue:
                penalty_amount = invoice.amount * 0.10  # 10% de pénalité
                
                penalty_vals = {
                    'invoice_type': 'penalty',
                    'contract_id': invoice.contract_id.id,
                    'partner_id': invoice.partner_id.id,
                    'amount': penalty_amount,
                    'period_start': invoice.period_start,
                    'period_end': invoice.period_end,
                    'invoice_date': fields.Date.today(),
                    'state': 'sent',
                    'name': f"PENAL-{invoice.name}"
                }
                
                self.env['soya.financial.invoice'].create(penalty_vals)
    
    # === MÉTHODES CRON ===
    @api.model
    def _cron_check_overdue_invoices(self):
        """Cron job pour vérifier les factures en retard"""
        today = fields.Date.today()
        overdue_invoices = self.search([
            ('state', '=', 'sent'),
            ('due_date', '<', today)
        ])
        
        for invoice in overdue_invoices:
            invoice.state = 'overdue'
            _logger.info(f"Facture {invoice.name} marquée comme en retard")
        
        return len(overdue_invoices)