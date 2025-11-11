{
    'name': "SOYA Agence Immobilière",
    'summary': "Gestion complète des biens immobiliers, offres et agents pour l'agence SOYA.",
    
    'description': """
    Gestion Immobilière Complète:
    - Fiches de biens immobiliers (appartements, maisons, terrains).
    - Suivi du cycle de vie des biens (Nouveau, Offre Reçue, Vendu, Annulé).
    - Gestion des offres d'achat/location.
    - Intégration des fonctionnalités de communication (Chatter) et d'activités.
    """,
    
    'author': "Votre Nom",
    'website': "http://www.soya-immobilier.com",
    'category': 'Industries/Real Estate',
    'version': '17.0.1.0.0',
    
    # DÉPENDANCES
    # 'base' est requis par Odoo, 'mail' est requis pour le Chatter et les activités.
    'depends': [
        'base', 
        'mail', 
        'website',
    ],

    
    
    # FICHIERS DE DONNÉES ET DE VUES À CHARGER
    # L'ordre est essentiel : Sécurité -> Données -> Vues -> Rapports
    'data': [
        # ========================
        # 1. SÉCURITÉ (Toujours en premier)

        'security/soya_estate_rules.xml',
        'security/ir.model.access.csv',
        
        # ========================
        # 2. SÉQUENCES (Avant les vues qui les utilisent)
  
        'data/sequences.xml',

        # ========================
        # 3. VUES PRINCIPALES (Par ordre logique)
        
        'views/property_views.xml',
        'views/property_type_views.xml',
        'views/property_offer_views.xml',
        'views/contract_views.xml',
        'views/contract_menus.xml',
        
        # ========================
        # 4. VUES WEB ET WIZARDS
        'views/property_web_templates.xml',
        'wizards/close_property_views.xml',
        
        
    ],

    'demo': [
        'demo/property_type_demo.xml',
    ],



    'assets': {
        'web.assets_backend': [
            'soya_estate/static/src/css/soya_estate.css',
        ],
    },
    
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
} # type: ignore
