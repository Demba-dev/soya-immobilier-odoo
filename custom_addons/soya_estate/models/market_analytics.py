from odoo import models, fields, api
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from statistics import mean, stdev


class SoyaMarketAnalytics(models.Model):
    _name = 'soya.market.analytics'
    _description = 'Analytics Prédictives du Marché'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'analysis_date desc'

    name = fields.Char(string="Référence", readonly=True, compute='_compute_name', store=True)
    
    analysis_date = fields.Date(string="Date Analyse", default=fields.Date.today, required=True)
    
    property_type_id = fields.Many2one(
        'soya.property.type',
        string='Type de Bien',
        tracking=True
    )
    
    location = fields.Char(string="Localisation", tracking=True)
    
    historical_period_months = fields.Integer(
        string="Période Historique (mois)",
        default=12,
        help="Nombre de mois utilisés pour les analyses"
    )
    
    avg_property_price = fields.Float(
        string="Prix Moyen Propriété",
        compute='_compute_market_data',
        store=True
    )
    
    price_trend = fields.Float(
        string="Tendance Prix (%)",
        compute='_compute_market_data',
        help="Évolution du prix moyen sur la période",
        store=True
    )
    
    price_volatility = fields.Float(
        string="Volatilité Prix",
        compute='_compute_market_data',
        help="Écart-type des prix",
        store=True
    )
    
    listings_count = fields.Integer(
        string="Annonces Actives",
        compute='_compute_market_activity',
        store=True
    )
    
    avg_days_on_market = fields.Float(
        string="Jours sur Marché Moyen",
        compute='_compute_market_activity',
        store=True
    )
    
    absorption_rate = fields.Float(
        string="Taux d'Absorption (%)",
        compute='_compute_market_activity',
        help="% de propriétés vendues par mois",
        store=True
    )
    
    sale_velocity = fields.Float(
        string="Vélocité Vente (jours)",
        compute='_compute_market_activity',
        store=True
    )
    
    demand_level = fields.Selection([
        ('very_high', 'Très Forte'),
        ('high', 'Forte'),
        ('moderate', 'Modérée'),
        ('low', 'Faible'),
        ('very_low', 'Très Faible'),
    ], string="Niveau Demande", compute='_compute_supply_demand', store=True)
    
    supply_level = fields.Selection([
        ('very_high', 'Très Important'),
        ('high', 'Important'),
        ('moderate', 'Modéré'),
        ('low', 'Faible'),
        ('very_low', 'Très Faible'),
    ], string="Niveau Offre", compute='_compute_supply_demand', store=True)
    
    market_balance = fields.Float(
        string="Équilibre Marché",
        compute='_compute_supply_demand',
        help="Ratio Demande/Offre",
        store=True
    )
    
    predicted_price_3m = fields.Float(
        string="Prix Prédit (3 mois)",
        compute='_compute_predictions',
        store=True
    )
    
    predicted_price_6m = fields.Float(
        string="Prix Prédit (6 mois)",
        compute='_compute_predictions',
        store=True
    )
    
    predicted_price_12m = fields.Float(
        string="Prix Prédit (12 mois)",
        compute='_compute_predictions',
        store=True
    )
    
    price_prediction_confidence = fields.Float(
        string="Confiance Prédiction (%)",
        compute='_compute_predictions',
        store=True
    )
    
    recommendation = fields.Selection([
        ('strong_buy', 'Achat Recommandé'),
        ('buy', 'Achat Possible'),
        ('hold', 'Maintenir'),
        ('sell', 'Vendre'),
        ('strong_sell', 'Vendre Rapidement'),
    ], string="Recommandation", compute='_compute_recommendation', store=True)
    
    recommendation_reason = fields.Text(
        string="Raison",
        compute='_compute_recommendation',
        store=True
    )
    
    risk_level = fields.Selection([
        ('very_low', 'Très Faible'),
        ('low', 'Faible'),
        ('moderate', 'Modéré'),
        ('high', 'Élevé'),
        ('very_high', 'Très Élevé'),
    ], string="Niveau Risque", compute='_compute_risk', store=True)
    
    opportunity_score = fields.Float(
        string="Score Opportunité",
        compute='_compute_risk',
        help="Score de 0 à 100",
        store=True
    )

    @api.depends('property_type_id', 'location', 'analysis_date')
    def _compute_name(self):
        for analytics in self:
            type_label = analytics.property_type_id.name if analytics.property_type_id else 'Général'
            location_label = f" - {analytics.location}" if analytics.location else ''
            date_label = analytics.analysis_date.strftime('%b %Y') if analytics.analysis_date else ''
            analytics.name = f"Analyse {type_label}{location_label} ({date_label})"
    
    def _validate_date(self, date_field):
        return date_field and isinstance(date_field, date)
    
    @api.depends('property_type_id', 'location', 'analysis_date', 'historical_period_months')
    def _compute_market_data(self):
        for analytics in self:
            if not self._validate_date(analytics.analysis_date):
                analytics.avg_property_price = 0
                analytics.price_trend = 0
                analytics.price_volatility = 0
                continue
            
            period_start = analytics.analysis_date - relativedelta(months=analytics.historical_period_months)
            
            domain = [
                ('create_date', '>=', datetime.combine(period_start, datetime.min.time())),
                ('create_date', '<=', datetime.combine(analytics.analysis_date, datetime.max.time())),
            ]
            
            if analytics.property_type_id:
                domain.append(('property_type_id', '=', analytics.property_type_id.id))
            
            properties = self.env['soya.property'].search(domain)
            
            if properties:
                prices = [p.expected_price for p in properties if p.expected_price]
                analytics.avg_property_price = mean(prices) if prices else 0
                analytics.price_volatility = stdev(prices) if len(prices) > 1 else 0
                
                current_prices = [p.expected_price for p in properties.filtered(
                    lambda x: x.create_date.date() >= analytics.analysis_date - relativedelta(months=1)
                ) if p.expected_price]
                old_prices = [p.expected_price for p in properties.filtered(
                    lambda x: x.create_date.date() < analytics.analysis_date - relativedelta(months=1)
                ) if p.expected_price]
                
                if current_prices and old_prices:
                    analytics.price_trend = ((mean(current_prices) - mean(old_prices)) / mean(old_prices) * 100)
                else:
                    analytics.price_trend = 0
            else:
                analytics.avg_property_price = 0
                analytics.price_trend = 0
                analytics.price_volatility = 0
    
    @api.depends('property_type_id', 'location', 'analysis_date')
    def _compute_market_activity(self):
        for analytics in self:
            if not self._validate_date(analytics.analysis_date):
                analytics.listings_count = 0
                analytics.absorption_rate = 0
                analytics.avg_days_on_market = 0
                analytics.sale_velocity = 0
                continue
            
            period_start = analytics.analysis_date - relativedelta(months=3)
            
            domain = [
                ('create_date', '>=', datetime.combine(period_start, datetime.min.time())),
                ('create_date', '<=', datetime.combine(analytics.analysis_date, datetime.max.time())),
                ('state', '=', 'new'),
            ]
            
            if analytics.property_type_id:
                domain.append(('property_type_id', '=', analytics.property_type_id.id))
            
            properties = self.env['soya.property'].search(domain)
            analytics.listings_count = len(properties)
            
            offers_domain = domain.copy()
            offers_domain.pop()
            offers = self.env['soya.property.offer'].search(offers_domain)
            analytics.absorption_rate = (len(offers) / max(1, len(properties)) * 100) if properties else 0
            
            if offers:
                days_list = [(o.create_date - o.property_id.create_date).days for o in offers if o.property_id]
                analytics.avg_days_on_market = mean(days_list) if days_list else 0
                analytics.sale_velocity = mean(days_list) if days_list else 0
            else:
                analytics.avg_days_on_market = 0
                analytics.sale_velocity = 0
    
    @api.depends()
    def _compute_supply_demand(self):
        for analytics in self:
            if not self._validate_date(analytics.analysis_date):
                analytics.demand_level = 'moderate'
                analytics.supply_level = 'moderate'
                analytics.market_balance = 1.0
                continue
            
            available_count = self.env['soya.property'].search_count([
                ('state', '=', 'available')
            ])
            
            interested_prospects = self.env['soya.prospect'].search_count([
                ('status', 'in', ['contacted', 'qualified']),
                ('create_date', '>=', datetime.combine(analytics.analysis_date - relativedelta(months=3), datetime.min.time()))
            ])
            
            analytics.demand_level = 'high' if interested_prospects > available_count else 'moderate'
            analytics.supply_level = 'high' if available_count > 10 else 'moderate'
            analytics.market_balance = interested_prospects / max(1, available_count)
    
    @api.depends('avg_property_price', 'price_trend', 'price_volatility')
    def _compute_predictions(self):
        for analytics in self:
            if not analytics.avg_property_price:
                analytics.predicted_price_3m = 0
                analytics.predicted_price_6m = 0
                analytics.predicted_price_12m = 0
                analytics.price_prediction_confidence = 0
                continue
            
            monthly_trend = analytics.price_trend / 12 if analytics.price_trend else 0
            
            analytics.predicted_price_3m = analytics.avg_property_price * (1 + (monthly_trend * 3) / 100)
            analytics.predicted_price_6m = analytics.avg_property_price * (1 + (monthly_trend * 6) / 100)
            analytics.predicted_price_12m = analytics.avg_property_price * (1 + (monthly_trend * 12) / 100)
            
            analytics.price_prediction_confidence = min(95, 100 - (analytics.price_volatility / analytics.avg_property_price * 100 if analytics.avg_property_price else 0))
    
    @api.depends('market_balance', 'price_trend', 'absorption_rate', 'risk_level')
    def _compute_recommendation(self):
        for analytics in self:
            score = 0
            reason = ""
            
            if analytics.market_balance > 1.5:
                score += 20
                reason += "Forte demande. "
            elif analytics.market_balance < 0.5:
                score -= 20
                reason += "Offre excédentaire. "
            
            if analytics.price_trend > 5:
                score += 15
                reason += "Prix en hausse. "
            elif analytics.price_trend < -5:
                score -= 15
                reason += "Prix en baisse. "
            
            if analytics.absorption_rate > 30:
                score += 15
                reason += "Absorption rapide. "
            
            if score > 40:
                analytics.recommendation = 'strong_buy'
            elif score > 20:
                analytics.recommendation = 'buy'
            elif score > -20:
                analytics.recommendation = 'hold'
            elif score > -40:
                analytics.recommendation = 'sell'
            else:
                analytics.recommendation = 'strong_sell'
            
            analytics.recommendation_reason = reason
    
    @api.depends('price_volatility', 'market_balance', 'avg_days_on_market')
    def _compute_risk(self):
        for analytics in self:
            risk_score = 50
            
            if analytics.price_volatility > 100000:
                risk_score += 20
            elif analytics.price_volatility < 50000:
                risk_score -= 10
            
            if analytics.market_balance < 0.5:
                risk_score += 15
            
            if analytics.avg_days_on_market > 180:
                risk_score += 10
            
            if risk_score > 75:
                analytics.risk_level = 'very_high'
            elif risk_score > 60:
                analytics.risk_level = 'high'
            elif risk_score > 40:
                analytics.risk_level = 'moderate'
            elif risk_score > 25:
                analytics.risk_level = 'low'
            else:
                analytics.risk_level = 'very_low'
            
            analytics.opportunity_score = 100 - (risk_score / 2)
