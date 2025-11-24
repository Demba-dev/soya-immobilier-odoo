from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta

class SoyaProperty(models.Model):
    _name = 'soya.property'
    _description = 'Bien Immobilier SOYA'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    # === CHAMPS PRINCIPAUX ===
    name = fields.Char(string="Titre du Bien", required=True, tracking=True)
    image = fields.Image(string="Image", copy=False)
    expected_price = fields.Float(string="Prix Attendu", required=True, tracking=True)
    selling_price = fields.Float(string="Prix de Vente", readonly=True, copy=False, tracking=True)
    
    # Lien vers le Type de Bien (Many2one)
    property_type_id = fields.Many2one(
        'soya.property.type', 
        string="Type de Bien",
        required=True,
        tracking=True
    )

    # Lien vers les Offres (One2many)
    offer_ids = fields.One2many(
        'soya.property.offer',  
        'property_id',          
        string='Offres Reçues'
    )
    
    # Agent Immobilier (pour la règle de sécurité)
    salesperson_id = fields.Many2one(
        'res.users', 
        string='Agent Immobilier', 
        default=lambda self: self.env.user,
        tracking=True
    )

    state = fields.Selection([
        ('new', 'Nouveau'),
        ('offer_received', 'Offre Reçue'),
        ('offer_accepted', 'Offre Acceptée'),
        ('sold', 'Vendu'),
        ('canceled', 'Annulé'),
        ('rented', 'Loué'),  # NOUVEAU
        ('maintenance', 'En Maintenance'),  # NOUVEAU
    ], string='Statut', default='new', copy=False, tracking=True)
    
    # === NOUVEAUX CHAMPS - LOCALISATION MALI ===
    street = fields.Char(string="Rue/Avenue", tracking=True)
    quarter = fields.Selection([
        ('badalabougou', 'Badalabougou'),
        ('niamakoro', 'Niamakoro'), 
        ('hippodrome', 'Hippodrome'),
        ('aci2000', 'ACI 2000'),
        ('quartier_du_fleuve', 'Quartier du Fleuve'),
        ('commune_i', 'Commune I'),
        ('commune_ii', 'Commune II'),
        ('commune_iii', 'Commune III'),
        ('commune_iv', 'Commune IV'),
        ('commune_v', 'Commune V'),
        ('commune_vi', 'Commune VI'),
        ('autres', 'Autres communes')
    ], string="Quartier", required=True, tracking=True)
    
    city = fields.Char(string="Ville", default="Bamako", tracking=True)
    country_id = fields.Many2one(
        'res.country', 
        string="Pays", 
        default=lambda self: self.env.ref('base.ml')
    )
    gps_coordinates = fields.Char(string="Coordonnées GPS")
    
    # === CARACTÉRISTIQUES PHYSIQUES ===
    living_area = fields.Float(string="Surface habitable (m²)", tracking=True)
    land_area = fields.Float(string="Surface du terrain (m²)", tracking=True)
    total_area = fields.Float(
        string="Surface totale (m²)",
        compute='_compute_total_area'
    )
    
    bedrooms = fields.Integer(string="Nombre de chambres", tracking=True)
    bathrooms = fields.Integer(string="Salles de bain", tracking=True)
    toilets = fields.Integer(string="Toilettes", tracking=True)
    
    # Équipements
    has_garage = fields.Boolean(string="Garage")
    has_garden = fields.Boolean(string="Jardin")
    has_pool = fields.Boolean(string="Piscine")
    has_ac = fields.Boolean(string="Climatisation")
    furnished = fields.Boolean(string="Meublé")
    security_system = fields.Boolean(string="Système de sécurité")
    
    construction_year = fields.Integer(string="Année de construction")
    
    # === INFORMATIONS LÉGALES (SPÉCIFIQUE MALI) ===
    land_title_number = fields.Char(string="Numéro titre foncier", tracking=True)
    land_title_date = fields.Date(string="Date titre foncier")
    land_title_status = fields.Selection([
        ('certified', 'Titre certifié'),
        ('pending', 'En cours de régularisation'),
        ('customary', 'Droit coutumier'),
        ('none', 'Aucun titre')
    ], string="Statut titre", default='none', tracking=True)
    
    # === GESTION LOCATIVE (NOUVEAU) ===
    rent_price = fields.Float(string="Prix location/mois (FCFA)", tracking=True)
    rental_deposit = fields.Float(string="Dépôt de garantie (FCFA)")
    availability_date = fields.Date(string="Date de disponibilité")
    
    # Relations locatives
    owner_id = fields.Many2one(
        'res.partner',
        string="Propriétaire",
        required=True,
        tracking=True
    )
    current_tenant_id = fields.Many2one(
        'res.partner',
        string="Locataire Actuel"
    )
    
    # === COMPTEURS ET STATISTIQUES ===
    visit_count = fields.Integer(
        string="Nombre de visites",
        default=0,
        tracking=True
    )
    offer_count = fields.Integer(
        string="Nombre d'offres",
        compute='_compute_offer_count',
        store=True
    )
    best_offer = fields.Float(
        string="Meilleure offre",
        compute='_compute_best_offer'
    )
    
    # === CHAMPS CALCULÉS ===
    @api.depends('living_area', 'land_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.land_area
    
    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)
    
    @api.depends('offer_ids.price')
    def _compute_best_offer(self):
        for record in self:
            valid_offers = record.offer_ids.filtered(
                lambda o: o.state in ['submitted', 'accepted']
            )
            record.best_offer = max(valid_offers.mapped('price')) if valid_offers else 0.0
    
    # === CONTRAINTES ET VALIDATIONS ===
    @api.constrains('expected_price', 'rent_price')
    def _check_positive_prices(self):
        for record in self:
            if record.expected_price < 0:
                raise ValidationError("Le prix attendu doit être positif")
            if record.rent_price < 0:
                raise ValidationError("Le prix de location doit être positif")
    
    @api.constrains('construction_year')
    def _check_construction_year(self):
        for record in self:
            if record.construction_year and record.construction_year > date.today().year:
                raise ValidationError("L'année de construction ne peut pas être dans le futur")

    # === ACTIONS (MÉTHODES) ===
    def action_view_offers(self):
        """Action pour le smart button des offres."""
        return {
            'type': 'ir.actions.act_window',
            'name': f"Offres pour {self.name}",
            'domain': [('property_id', '=', self.id)],
            'view_mode': 'tree,form',
            'res_model': 'soya.property.offer',
            'target': 'current',
        }

    def action_mark_sold(self):
        """Marquer le bien comme vendu"""
        for record in self:
            if record.state != 'offer_accepted':
                raise ValidationError("Seuls les biens avec offre acceptée peuvent être marqués comme vendus")
            record.state = 'sold'
            record.selling_price = record.best_offer
    
    def action_mark_rented(self):
        """Marquer le bien comme loué"""
        for record in self:
            record.state = 'rented'
    
    def action_reset_to_new(self):
        """Réinitialiser le statut du bien"""
        for record in self:
            record.state = 'new'
    
    def action_schedule_visit(self):
        """Ouvrir le wizard de planification de visite"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Planifier Visite',
            'res_model': 'soya.visit',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_property_id': self.id}
        }
    
    # === MÉTHODES TECHNIQUES ===
    def _generate_property_code(self):
        """Générer un code unique pour le bien"""
        return self.env['ir.sequence'].next_by_code('soya.property.sequence') or 'Nouveau Bien'
    
    # === SURCHARGE DES MÉTHODES STANDARD ===
    @api.model
    def create(self, vals):
        """Surcharge de la création pour générer le nom si vide"""
        if not vals.get('name') or vals.get('name') == 'Nouveau Bien':
            vals['name'] = self._generate_property_code()
        return super().create(vals)