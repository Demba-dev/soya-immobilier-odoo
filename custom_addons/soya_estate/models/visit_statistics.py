from odoo import models, fields, api
from datetime import date, timedelta, datetime


class SoyaVisitStatistics(models.Model):
    _name = 'soya.visit.statistics'
    _description = 'Statistiques des Visites'
    _auto = False
    _rec_name = 'agent_id'

    agent_id = fields.Many2one('res.users', string="Agent", readonly=True)
    property_id = fields.Many2one('soya.property', string="Bien", readonly=True)
    
    # Statistiques
    total_visits = fields.Integer(string="Total Visites", readonly=True)
    completed_visits = fields.Integer(string="Visites Complétées", readonly=True)
    no_show_visits = fields.Integer(string="Non-Présentations", readonly=True)
    cancelled_visits = fields.Integer(string="Visites Annulées", readonly=True)
    
    # Conversion
    converted_visits = fields.Integer(string="Visites Converties", readonly=True)
    conversion_rate = fields.Float(string="Taux de Conversion (%)", readonly=True, digits=(5, 2))
    
    # Intérêt
    very_interested_count = fields.Integer(string="Très Intéressés", readonly=True)
    interested_count = fields.Integer(string="Intéressés", readonly=True)
    not_interested_count = fields.Integer(string="Pas Intéressés", readonly=True)
    
    # Dates
    first_visit_date = fields.Date(string="Première Visite", readonly=True)
    last_visit_date = fields.Date(string="Dernière Visite", readonly=True)
    
    # Moyenne
    avg_quality_score = fields.Float(string="Score Qualité Moyen", readonly=True, digits=(3, 2))
    
    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW soya_visit_statistics AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY sv.salesperson_id, sv.property_id) as id,
                    sv.salesperson_id as agent_id,
                    sv.property_id,
                    COUNT(*) as total_visits,
                    COUNT(CASE WHEN sv.state = 'completed' THEN 1 END) as completed_visits,
                    COUNT(CASE WHEN sv.state = 'no_show' THEN 1 END) as no_show_visits,
                    COUNT(CASE WHEN sv.state = 'cancelled' THEN 1 END) as cancelled_visits,
                    COUNT(CASE WHEN sv.converted_to_offer = true THEN 1 END) as converted_visits,
                    CASE 
                        WHEN COUNT(*) = 0 THEN 0
                        ELSE ROUND(100.0 * COUNT(CASE WHEN sv.converted_to_offer = true THEN 1 END) / COUNT(*), 2)
                    END as conversion_rate,
                    COUNT(CASE WHEN sv.prospect_interest = 'very_interested' THEN 1 END) as very_interested_count,
                    COUNT(CASE WHEN sv.prospect_interest = 'interested' THEN 1 END) as interested_count,
                    COUNT(CASE WHEN sv.prospect_interest = 'not_interested' THEN 1 END) as not_interested_count,
                    MIN(sv.visit_date::date) as first_visit_date,
                    MAX(sv.visit_date::date) as last_visit_date,
                    ROUND(AVG(CASE WHEN sv.quality_score > 0 THEN sv.quality_score ELSE NULL END), 2) as avg_quality_score
                FROM soya_visit sv
                WHERE sv.state NOT IN ('cancelled')
                GROUP BY sv.salesperson_id, sv.property_id
            )
        """)


class SoyaConversionStatistics(models.Model):
    _name = 'soya.conversion.statistics'
    _description = 'Statistiques de Conversion Prospects'
    _auto = False
    _rec_name = 'agent_id'

    agent_id = fields.Many2one('res.users', string="Agent", readonly=True)
    
    # Prospects
    total_prospects = fields.Integer(string="Total Prospects", readonly=True)
    new_prospects = fields.Integer(string="Nouveaux", readonly=True)
    contacted_prospects = fields.Integer(string="Contactés", readonly=True)
    qualified_prospects = fields.Integer(string="Qualifiés", readonly=True)
    converted_prospects = fields.Integer(string="Convertis", readonly=True)
    lost_prospects = fields.Integer(string="Perdus", readonly=True)
    
    # Statistiques
    conversion_rate = fields.Float(string="Taux de Conversion (%)", readonly=True, digits=(5, 2))
    loss_rate = fields.Float(string="Taux de Perte (%)", readonly=True, digits=(5, 2))
    avg_visits_per_prospect = fields.Float(string="Visites Moyennes par Prospect", readonly=True, digits=(3, 2))
    
    # Dates
    period_start = fields.Date(string="Période Début", readonly=True)
    period_end = fields.Date(string="Période Fin", readonly=True)

    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW soya_conversion_statistics AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY sp.salesperson_id) as id,
                    sp.salesperson_id as agent_id,
                    COUNT(*) as total_prospects,
                    COUNT(CASE WHEN sp.state = 'new' THEN 1 END) as new_prospects,
                    COUNT(CASE WHEN sp.state = 'contacted' THEN 1 END) as contacted_prospects,
                    COUNT(CASE WHEN sp.state = 'qualified' THEN 1 END) as qualified_prospects,
                    COUNT(CASE WHEN sp.state = 'converted' THEN 1 END) as converted_prospects,
                    COUNT(CASE WHEN sp.state = 'lost' THEN 1 END) as lost_prospects,
                    CASE 
                        WHEN COUNT(*) = 0 THEN 0
                        ELSE ROUND(100.0 * COUNT(CASE WHEN sp.state = 'converted' THEN 1 END) / COUNT(*), 2)
                    END as conversion_rate,
                    CASE 
                        WHEN COUNT(*) = 0 THEN 0
                        ELSE ROUND(100.0 * COUNT(CASE WHEN sp.state = 'lost' THEN 1 END) / COUNT(*), 2)
                    END as loss_rate,
                    ROUND(AVG(sp.visit_count)::numeric, 2) as avg_visits_per_prospect,
                    DATE(MIN(sp.create_date)) as period_start,
                    DATE(MAX(sp.create_date)) as period_end
                FROM soya_prospect sp
                GROUP BY sp.salesperson_id
            )
        """)
