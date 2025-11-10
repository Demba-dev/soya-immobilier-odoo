from odoo import http
from odoo.http import request

class SoyaEstateController(http.Controller):

    @http.route('/properties', type='http', auth='public', website=True)
    def properties_list(self, **kwargs):
        """
        Contrôleur pour afficher la liste publique des biens immobiliers.
        """
        # Récupérer les biens qui sont dans l'état 'Nouveau' (disponibles)
        properties = request.env['soya.property'].search([
            ('state', '=', 'new')
        ])
        
        # Préparer les valeurs à envoyer au template
        values = {
            'properties': properties,
            'page_title': 'Nos Biens Immobiliers'
        }
        
        # Rendre le template QWeb et lui passer les valeurs
        return request.render('soya_estate.properties_list_template', values)

    @http.route('/properties/<model("soya.property"):property>', type='http', auth='public', website=True)
    def property_details(self, property, **kwargs):
        """
        Contrôleur pour afficher la page de détail d'un bien immobilier.
        """
        return request.render('soya_estate.property_details_template', {
            'property': property,
            'page_title': property.name
        })
