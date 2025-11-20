from odoo import models, fields, api
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


class SoyaPerformanceKPI(models.Model):
    _name = 'soya.performance.kpi'
    _description = 'Indicateurs de Performance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'period_end desc'

    name = fields.Char(string="Référence KPI", readonly=True, compute='_compute_name', store=True)
    
    period_start = fields.Date(string="Début Période", required=True, tracking=True)
    period_end = fields.Date(string="Fin Période", required=True, tracking=True)
    
    agent_id = fields.Many2one(
        'res.users',
        string='Agent',
        tracking=True,
        help="Laisser vide pour les KPIs globaux"
    )
    
    total_offers = fields.Integer(
        string="Total Offres",
        compute='_compute_sales_kpis',
        help="Nombre total d'offres créées"
    )
    
    offers_accepted = fields.Integer(
        string="Offres Acceptées",
        compute='_compute_sales_kpis'
    )
    
    acceptance_rate = fields.Float(
        string="Taux d'Acceptation (%)",
        compute='_compute_sales_kpis'
    )
    
    total_revenue = fields.Float(
        string="Revenu Total",
        compute='_compute_revenue_kpis',
        help="Total des commissions et revenus"
    )
    
    avg_transaction_value = fields.Float(
        string="Valeur Transaction Moyenne",
        compute='_compute_revenue_kpis'
    )
    
    total_prospects = fields.Integer(
        string="Total Prospects",
        compute='_compute_prospect_kpis'
    )
    
    qualified_prospects = fields.Integer(
        string="Prospects Qualifiés",
        compute='_compute_prospect_kpis'
    )
    
    conversion_rate = fields.Float(
        string="Taux Conversion (%)",
        compute='_compute_prospect_kpis'
    )
    
    total_visits = fields.Integer(
        string="Total Visites",
        compute='_compute_visit_kpis'
    )
    
    completed_visits = fields.Integer(
        string="Visites Complétées",
        compute='_compute_visit_kpis'
    )
    
    avg_visit_quality = fields.Float(
        string="Qualité Visite Moyenne",
        compute='_compute_visit_kpis'
    )
    
    properties_available = fields.Integer(
        string="Biens Disponibles",
        compute='_compute_portfolio_kpis'
    )
    
    properties_rented = fields.Integer(
        string="Biens Loués",
        compute='_compute_portfolio_kpis'
    )
    
    portfolio_occupancy_rate = fields.Float(
        string="Taux d'Occupation (%)",
        compute='_compute_portfolio_kpis'
    )

    @api.depends('period_start', 'period_end', 'agent_id')
    def _compute_name(self):
        for kpi in self:
            period_label = f"{kpi.period_start.strftime('%b %Y')}" if kpi.period_start else ''
            agent_label = f" - {kpi.agent_id.name}" if kpi.agent_id else " - Global"
            kpi.name = f"KPI {period_label}{agent_label}"
    
    def _validate_dates(self, kpi):
        return (kpi.period_start and kpi.period_end and 
                isinstance(kpi.period_start, date) and 
                isinstance(kpi.period_end, date))
    
    @api.depends('period_start', 'period_end', 'agent_id')
    def _compute_sales_kpis(self):
        for kpi in self:
            if not self._validate_dates(kpi):
                kpi.total_offers = 0
                kpi.offers_accepted = 0
                kpi.acceptance_rate = 0
                continue
            
            domain = [
                ('create_date', '>=', datetime.combine(kpi.period_start, datetime.min.time())),
                ('create_date', '<=', datetime.combine(kpi.period_end, datetime.max.time())),
                ('state', '!=', 'cancelled'),
            ]
            
            if kpi.agent_id:
                domain.append(('salesperson_id', '=', kpi.agent_id.id))
            
            offers = self.env['soya.property.offer'].search(domain)
            kpi.total_offers = len(offers)
            kpi.offers_accepted = len(offers.filtered(lambda o: o.state == 'accepted'))
            kpi.acceptance_rate = (kpi.offers_accepted / kpi.total_offers * 100) if kpi.total_offers > 0 else 0
    
    @api.depends('period_start', 'period_end', 'agent_id')
    def _compute_revenue_kpis(self):
        for kpi in self:
            if not self._validate_dates(kpi):
                kpi.total_revenue = 0
                kpi.avg_transaction_value = 0
                continue
            
            domain = [
                ('create_date', '>=', datetime.combine(kpi.period_start, datetime.min.time())),
                ('create_date', '<=', datetime.combine(kpi.period_end, datetime.max.time())),
                ('state', 'in', ['active', 'done']),
            ]
            
            contracts = self.env['soya.sale.contract'].search(domain)
            
            total_revenue = sum(contract.sale_price for contract in contracts)
            kpi.total_revenue = total_revenue
            kpi.avg_transaction_value = (total_revenue / len(contracts)) if len(contracts) > 0 else 0
    
    @api.depends('period_start', 'period_end', 'agent_id')
    def _compute_prospect_kpis(self):
        for kpi in self:
            if not self._validate_dates(kpi):
                kpi.total_prospects = 0
                kpi.qualified_prospects = 0
                kpi.conversion_rate = 0
                continue
            
            domain = [
                ('create_date', '>=', datetime.combine(kpi.period_start, datetime.min.time())),
                ('create_date', '<=', datetime.combine(kpi.period_end, datetime.max.time())),
            ]
            
            if kpi.agent_id:
                domain.append(('salesperson_id', '=', kpi.agent_id.id))
            
            prospects = self.env['soya.prospect'].search(domain)
            kpi.total_prospects = len(prospects)
            kpi.qualified_prospects = len(prospects.filtered(lambda p: p.state in ['qualified', 'converted']))        
            kpi.conversion_rate = (kpi.qualified_prospects / kpi.total_prospects * 100) if kpi.total_prospects > 0 else 0
    
    @api.depends('period_start', 'period_end', 'agent_id')
    def _compute_visit_kpis(self):
        for kpi in self:
            if not self._validate_dates(kpi):
                kpi.total_visits = 0
                kpi.completed_visits = 0
                kpi.avg_visit_quality = 0
                continue
            
            domain = [
                ('visit_date', '>=', datetime.combine(kpi.period_start, datetime.min.time())),
                ('visit_date', '<=', datetime.combine(kpi.period_end, datetime.max.time())),
                ('state', '!=', 'cancelled'),
            ]
            
            if kpi.agent_id:
                domain.append(('salesperson_id', '=', kpi.agent_id.id))
            
            visits = self.env['soya.visit'].search(domain)
            kpi.total_visits = len(visits)
            kpi.completed_visits = len(visits.filtered(lambda v: v.state == 'completed'))
            
            quality_scores = [v.quality_score for v in visits if v.quality_score]
            kpi.avg_visit_quality = (sum(quality_scores) / len(quality_scores)) if quality_scores else 0
    
    @api.depends('period_start', 'period_end', 'agent_id')
    def _compute_portfolio_kpis(self):
        for kpi in self:
            properties = self.env['soya.property'].search([])
            
            kpi.properties_available = len(properties.filtered(lambda p: p.state == 'new'))
            kpi.properties_rented = len(properties.filtered(lambda p: p.state == 'rented'))
            
            total_properties = len(properties)
            kpi.portfolio_occupancy_rate = (kpi.properties_rented / total_properties * 100) if total_properties > 0 else 0
