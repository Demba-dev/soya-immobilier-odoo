from odoo import models, fields, api


class SoyaPropertyProfitability(models.Model):
    _name = 'soya.property.profitability'
    _description = 'Analyse de Rentabilité des Propriétés'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'property_id'

    name = fields.Char(string="Référence", readonly=True, compute='_compute_name', store=True)
    
    property_id = fields.Many2one(
        'soya.property',
        string='Bien Immobilier',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    total_rental_income = fields.Float(
        string="Revenu Locatif Total",
        compute='_compute_revenues',
        help="Revenu total des contrats de location"
    )
    
    total_sale_commissions = fields.Float(
        string="Commissions Vente",
        compute='_compute_revenues',
        help="Commissions générées par la vente"
    )
    
    total_revenue = fields.Float(
        string="Revenu Total",
        compute='_compute_revenues'
    )
    
    avg_monthly_rent = fields.Float(
        string="Loyer Mensuel Moyen",
        compute='_compute_revenues'
    )
    
    maintenance_costs = fields.Float(
        string="Frais d'Entretien",
        compute='_compute_expenses'
    )
    
    tax_expenses = fields.Float(
        string="Taxes et Impôts",
        compute='_compute_expenses'
    )
    
    insurance_costs = fields.Float(
        string="Coûts d'Assurance",
        compute='_compute_expenses'
    )
    
    other_expenses = fields.Float(
        string="Autres Charges",
        compute='_compute_expenses'
    )
    
    total_expenses = fields.Float(
        string="Total Charges",
        compute='_compute_expenses'
    )
    
    gross_profit = fields.Float(
        string="Profit Brut",
        compute='_compute_profitability'
    )
    
    net_profit = fields.Float(
        string="Profit Net",
        compute='_compute_profitability'
    )
    
    profit_margin = fields.Float(
        string="Marge Bénéficiaire (%)",
        compute='_compute_profitability'
    )
    
    roi = fields.Float(
        string="ROI (%)",
        compute='_compute_profitability',
        help="Retour sur investissement",
        store=True
    )
    
    annualized_roi = fields.Float(
        string="ROI Annualisé (%)",
        compute='_compute_profitability',
        store=True
    )
    
    vacancy_rate = fields.Float(
        string="Taux Vacance (%)",
        compute='_compute_occupancy',
        store=True
    )
    
    occupancy_months = fields.Integer(
        string="Mois d'Occupation",
        compute='_compute_occupancy',
        store=True
    )
    
    property_value = fields.Float(
        string="Valeur de la Propriété",
        related='property_id.expected_price',
        readonly=True
    )
    
    property_acquisition_price = fields.Float(
        string="Prix d'Acquisition",
        related='property_id.expected_price',
        readonly=True
    )
    
    appreciation = fields.Float(
        string="Appréciation Valeur",
        compute='_compute_appreciation'
    )
    
    appreciation_percentage = fields.Float(
        string="% Appréciation",
        compute='_compute_appreciation'
    )

    @api.depends('property_id')
    def _compute_name(self):
        for prof in self:
            prof.name = f"Rentabilité - {prof.property_id.name}" if prof.property_id else "Rentabilité"
    
    @api.depends('property_id')
    def _compute_revenues(self):
        for prof in self:
            if not prof.property_id:
                prof.total_rental_income = 0
                prof.total_sale_commissions = 0
                prof.total_revenue = 0
                prof.avg_monthly_rent = 0
                continue
            
            rental_contracts = self.env['soya.rental.contract'].search([
                ('property_id', '=', prof.property_id.id),
                ('state', 'in', ['active', 'done'])
            ])
            
            sale_contracts = self.env['soya.sale.contract'].search([
                ('property_id', '=', prof.property_id.id),
                ('state', 'in', ['active', 'done'])
            ])
            
            prof.total_rental_income = sum(c.monthly_rent * c.duration_months for c in rental_contracts)
            prof.total_sale_commissions = sum(c.sale_price * 0.05 for c in sale_contracts)
            prof.total_revenue = prof.total_rental_income + prof.total_sale_commissions
            
            active_rentals = rental_contracts.filtered(lambda c: c.state == 'active')
            if active_rentals:
                prof.avg_monthly_rent = sum(c.monthly_rent for c in active_rentals) / len(active_rentals)
            else:
                prof.avg_monthly_rent = 0
    
    @api.depends('property_id')
    def _compute_expenses(self):
        for prof in self:
            if not prof.property_id:
                prof.maintenance_costs = 0
                prof.tax_expenses = 0
                prof.insurance_costs = 0
                prof.other_expenses = 0
                prof.total_expenses = 0
                continue
            
            invoices = self.env['soya.financial.invoice'].search([
                ('property_id', '=', prof.property_id.id),
                ('invoice_type', '=', 'expense')
            ])
            
            prof.maintenance_costs = sum(i.amount for i in invoices.filtered(lambda x: x.category == 'maintenance'))
            prof.tax_expenses = sum(i.amount for i in invoices.filtered(lambda x: x.category == 'taxes'))
            prof.insurance_costs = sum(i.amount for i in invoices.filtered(lambda x: x.category == 'insurance'))
            prof.other_expenses = sum(i.amount for i in invoices.filtered(lambda x: x.category not in ['maintenance', 'taxes', 'insurance']))
            prof.total_expenses = prof.maintenance_costs + prof.tax_expenses + prof.insurance_costs + prof.other_expenses
    
    @api.depends('total_revenue', 'total_expenses', 'property_acquisition_price')
    def _compute_profitability(self):
        for prof in self:
            prof.gross_profit = prof.total_revenue - prof.total_expenses
            prof.net_profit = prof.gross_profit
            
            prof.profit_margin = (prof.net_profit / prof.total_revenue * 100) if prof.total_revenue > 0 else 0
            prof.roi = (prof.net_profit / prof.property_acquisition_price * 100) if prof.property_acquisition_price > 0 else 0
            prof.annualized_roi = prof.roi * 12 if prof.roi else 0
    
    @api.depends('property_id')
    def _compute_occupancy(self):
        for prof in self:
            if not prof.property_id:
                prof.vacancy_rate = 0
                prof.occupancy_months = 0
                continue
            
            rental_contracts = self.env['soya.rental.contract'].search([
                ('property_id', '=', prof.property_id.id),
                ('state', 'in', ['active', 'done'])
            ])
            
            if rental_contracts:
                occupied_months = len(rental_contracts)
                prof.occupancy_months = occupied_months
                prof.vacancy_rate = max(0, 12 - occupied_months) / 12 * 100
            else:
                prof.vacancy_rate = 100
                prof.occupancy_months = 0
    
    @api.depends('property_id')
    def _compute_appreciation(self):
        for prof in self:
            if prof.property_id:
                current_value = prof.property_id.selling_price if prof.property_id.selling_price else prof.property_id.expected_price
                acquisition_price = prof.property_id.expected_price
                prof.appreciation = current_value - acquisition_price
                prof.appreciation_percentage = (prof.appreciation / acquisition_price * 100) if acquisition_price else 0
            else:
                prof.appreciation = 0
                prof.appreciation_percentage = 0
