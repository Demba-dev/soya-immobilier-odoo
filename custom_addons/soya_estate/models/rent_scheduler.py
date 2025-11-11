from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class SoyaRentScheduler(models.Model):
    _name = 'soya.rent.scheduler'
    _description = 'Gestionnaire Automatique des Loyers'
    
    @api.model
    def _cron_generate_monthly_rent_invoices(self):
        """
        Cron job pour générer automatiquement les quittances de loyer mensuelles
        S'exécute le 25 de chaque mois pour le mois suivant
        """
        today = fields.Date.today()
        
        # Générer pour le mois suivant
        if today.day == 25:
            next_month = today.replace(day=28) + timedelta(days=4)  # Va au mois suivant
            month_start = next_month.replace(day=1)
            next_next_month = (month_start + timedelta(days=32)).replace(day=1)
            month_end = next_next_month - timedelta(days=1)
            
            return self._generate_rent_invoices_for_month(month_start, month_end)
        return "Pas d'exécution aujourd'hui"
    
    def _generate_rent_invoices_for_month(self, month_start, month_end):
        """Génère les quittances de loyer pour un mois donné"""
        # Trouver tous les contrats de location actifs
        active_contracts = self.env['soya.rental.contract'].search([
            ('state', '=', 'active'),
            ('start_date', '<=', month_end),
            '|', ('end_date', '=', False), ('end_date', '>=', month_start)
        ])
        
        invoices_created = 0
        
        for contract in active_contracts:
            # Vérifier si une facture existe déjà pour cette période
            existing_invoice = self.env['soya.financial.invoice'].search([
                ('contract_id', '=', contract.id),
                ('period_start', '=', month_start),
                ('period_end', '=', month_end),
                ('invoice_type', '=', 'rent')
            ], limit=1)
            
            if not existing_invoice:
                try:
                    # Calculer le montant (loyer + charges)
                    total_amount = contract.monthly_rent + contract.charges_amount
                    
                    # Créer la quittance de loyer
                    invoice_vals = {
                        'invoice_type': 'rent',
                        'contract_id': contract.id,
                        'partner_id': contract.tenant_id.id,
                        'amount': total_amount,
                        'period_start': month_start,
                        'period_end': month_end,
                        'invoice_date': fields.Date.today(),
                        'state': 'sent',
                        'name': f"QUIT-{contract.name}-{month_start.strftime('%Y%m')}"
                    }
                    
                    self.env['soya.financial.invoice'].create(invoice_vals)
                    invoices_created += 1
                    
                    _logger.info(f"Quittance générée pour {contract.name}")
                    
                except Exception as e:
                    _logger.error(f"Erreur génération quittance {contract.name}: {str(e)}")
        
        _logger.info(f"{invoices_created} quittance(s) de loyer générée(s) pour {month_start.strftime('%B %Y')}")
        return f"{invoices_created} quittance(s) de loyer générée(s)"
    
    def generate_test_invoices(self):
        """Méthode de test pour générer des factures manuellement"""
        today = fields.Date.today()
        month_start = today.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        
        return self._generate_rent_invoices_for_month(month_start, month_end)