from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SoyaPropertyType(models.Model):
    _name = 'soya.property.type'
    _description = 'Type de Bien Immobilier'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    
    # === CHAMPS EXISTANTS (CONSERVÉS) ===
    name = fields.Char(string="Type", required=True, tracking=True)
    property_ids = fields.One2many(
        'soya.property',        
        'property_type_id',     
        string="Biens Associés"
    )
    sequence = fields.Integer(string="Séquence", default=10, tracking=True)
    
    # === NOUVEAUX CHAMPS - CATÉGORISATION MALI ===
    category = fields.Selection([
        ('residential', 'Résidentiel'),
        ('commercial', 'Commercial'),
        ('land', 'Terrain'),
        ('luxury', 'Luxe/Haut standing'),
        ('office', 'Bureau'),
        ('industrial', 'Industriel'),
        ('agricultural', 'Agricole')
    ], string="Catégorie", required=True, default='residential', tracking=True)
    
    code = fields.Char(
        string="Code",
        required=True,
        help="Code court pour identification rapide (ex: VIL, APP, TER)"
    )
    
    # === CONFIGURATION COMMERCIALE ===
    sales_commission_rate = fields.Float(
        string="Commission vente (%)",
        default=5.0,
        help="Taux de commission par défaut pour les ventes"
    )
    
    rental_commission_rate = fields.Float(
        string="Commission location (%)", 
        default=1.0,
        help="Taux de commission par défaut pour les locations"
    )
    
    # === CARACTÉRISTIQUES PAR DÉFAUT ===
    default_living_area = fields.Float(
        string="Surface habitable par défaut (m²)",
        help="Surface typique pour ce type de bien"
    )
    
    default_bedrooms = fields.Integer(
        string="Chambres par défaut",
        help="Nombre de chambres typique"
    )
    
    default_bathrooms = fields.Integer(
        string="Salles de bain par défaut",
        help="Nombre de salles de bain typique"
    )
    
    # === RÈGLES MÉTIER SPÉCIFIQUES ===
    requires_land_title = fields.Boolean(
        string="Nécessite titre foncier",
        default=True,
        help="Si ce type de bien nécessite obligatoirement un titre foncier au Mali"
    )
    
    max_floors = fields.Integer(
        string="Étages maximum",
        default=1,
        help="Nombre maximum d'étages pour ce type (R+ pour immeubles)"
    )
    
    is_rentable = fields.Boolean(
        string="Louable",
        default=True,
        help="Ce type de bien peut-il être mis en location ?"
    )
    
    is_sellable = fields.Boolean(
        string="Vendable", 
        default=True,
        help="Ce type de bien peut-il être mis en vente ?"
    )
    
    # === COMPTEURS AUTOMATIQUES ===
    property_count = fields.Integer(
        string="Nombre de biens",
        compute='_compute_property_count',
        store=True
    )
    
    available_property_count = fields.Integer(
        string="Biens disponibles",
        compute='_compute_available_property_count'
    )
    
    total_sales_value = fields.Float(
        string="Valeur totale des ventes (FCFA)",
        compute='_compute_total_sales_value'
    )
    
    # === MÉTADONNÉES ET DESCRIPTION ===
    description = fields.Text(
        string="Description du type",
        help="Description détaillée et caractéristiques spécifiques"
    )
    
    active = fields.Boolean(
        string="Actif",
        default=True,
        help="Désactiver pour masquer ce type sans supprimer les données"
    )
    
    # === CHAMPS CALCULÉS ===
    @api.depends('property_ids')
    def _compute_property_count(self):
        """Calcul du nombre total de biens de ce type"""
        for record in self:
            record.property_count = len(record.property_ids)
    
    @api.depends('property_ids.state')
    def _compute_available_property_count(self):
        """Calcul du nombre de biens disponibles"""
        for record in self:
            available_states = ['new', 'offer_received']
            record.available_property_count = len(
                record.property_ids.filtered(
                    lambda p: p.state in available_states
                )
            )
    
    @api.depends('property_ids.selling_price')
    def _compute_total_sales_value(self):
        """Calcul de la valeur totale des ventes réalisées"""
        for record in self:
            sold_properties = record.property_ids.filtered(
                lambda p: p.state == 'sold' and p.selling_price > 0
            )
            record.total_sales_value = sum(sold_properties.mapped('selling_price'))
    
    # === CONTRAINTES ET VALIDATIONS ===
    @api.constrains('sales_commission_rate', 'rental_commission_rate')
    def _check_commission_rates(self):
        """Vérifier que les taux de commission sont valides"""
        for record in self:
            if record.sales_commission_rate < 0 or record.sales_commission_rate > 100:
                raise ValidationError("Le taux de commission vente doit être entre 0% et 100%")
            if record.rental_commission_rate < 0 or record.rental_commission_rate > 100:
                raise ValidationError("Le taux de commission location doit être entre 0% et 100%")
    
    @api.constrains('code')
    def _check_code_unique(self):
        """Vérifier l'unicité du code"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(f"Le code '{record.code}' est déjà utilisé par un autre type")
    
    @api.constrains('default_living_area', 'default_bedrooms', 'default_bathrooms')
    def _check_default_values(self):
        """Vérifier la cohérence des valeurs par défaut"""
        for record in self:
            if record.default_living_area and record.default_living_area < 0:
                raise ValidationError("La surface par défaut ne peut pas être négative")
            if record.default_bedrooms and record.default_bedrooms < 0:
                raise ValidationError("Le nombre de chambres par défaut ne peut pas être négatif")
            if record.default_bathrooms and record.default_bathrooms < 0:
                raise ValidationError("Le nombre de salles de bain par défaut ne peut pas être négatif")
    
    # === MÉTHODES D'ACTION ===
    def action_view_properties(self):
        """Action pour voir tous les biens de ce type"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Biens - {self.name}',
            'res_model': 'soya.property',
            'view_mode': 'tree,form',
            'domain': [('property_type_id', '=', self.id)],
            'context': {'default_property_type_id': self.id}
        }
    
    def action_view_available_properties(self):
        """Action pour voir les biens disponibles de ce type"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Biens Disponibles - {self.name}',
            'res_model': 'soya.property',
            'view_mode': 'tree,form',
            'domain': [
                ('property_type_id', '=', self.id),
                ('state', 'in', ['new', 'offer_received'])
            ]
        }
    
    # === MÉTHODES TECHNIQUES ===
    @api.model
    def create(self, vals):
        """Surcharge de la création pour générer un code si vide"""
        if not vals.get('code'):
            # Générer un code basé sur le nom
            name = vals.get('name', '')
            code = ''.join([word[0].upper() for word in name.split()]) if name else 'TYP'
            vals['code'] = code
        return super().create(vals)
    
    def name_get(self):
        """Personnalisation de l'affichage du nom"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}" if record.code else record.name
            result.append((record.id, name))
        return result
    
    # === EXEMPLES DE TYPES PRÉDÉFINIS POUR LE MALI ===
    @api.model
    def _create_default_types(self):
        """Créer les types de biens courants au Mali"""
        default_types = [
            {
                'name': 'Villa',
                'code': 'VIL',
                'category': 'residential',
                'default_living_area': 150,
                'default_bedrooms': 3,
                'default_bathrooms': 2,
                'sales_commission_rate': 5.0,
                'requires_land_title': True
            },
            {
                'name': 'Appartement',
                'code': 'APP', 
                'category': 'residential',
                'default_living_area': 80,
                'default_bedrooms': 2,
                'default_bathrooms': 1,
                'sales_commission_rate': 4.0,
                'max_floors': 5
            },
            {
                'name': 'Terrain',
                'code': 'TER',
                'category': 'land', 
                'is_rentable': False,
                'default_living_area': 0,
                'sales_commission_rate': 8.0,
                'requires_land_title': True
            },
            {
                'name': 'Local Commercial',
                'code': 'COM',
                'category': 'commercial',
                'default_living_area': 50,
                'sales_commission_rate': 6.0,
                'rental_commission_rate': 1.5
            },
            {
                'name': 'Bureau',
                'code': 'BUR',
                'category': 'office',
                'default_living_area': 30,
                'sales_commission_rate': 4.0,
                'rental_commission_rate': 1.2
            }
        ]
        
        for type_vals in default_types:
            if not self.search_count([('code', '=', type_vals['code'])]):
                self.create(type_vals)

