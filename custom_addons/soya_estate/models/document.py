from odoo import models, fields, api

class SoyaContractDocument(models.Model):
    _name = 'soya.contract.document'
    _description = 'Document de Contrat SOYA'
    
    # Champs existants
    name = fields.Char(string='Nom du Document', required=True)
    contract_id = fields.Many2one('soya.base.contract', string='Contrat')
    document_file = fields.Binary(string='Fichier', required=True)
    document_filename = fields.Char(string='Nom du Fichier')
    upload_date = fields.Datetime(string='Date Upload', default=fields.Datetime.now)
    uploaded_by = fields.Many2one('res.users', string='Uploadé par', default=lambda self: self.env.user)
    
    # CHAMP MANQUANT - À AJOUTER
    document_type = fields.Selection([
        ('contrat_location', 'Contrat de Location'),
        ('contrat_vente', 'Contrat de Vente'),
        ('avenant', 'Avenant'),
        ('quittance', 'Quittance de Loyer'),
        ('etat_lieux', 'État des Lieux'),
        ('mandat', 'Mandat de Gestion'),
        ('piece_identite', 'Pièce d\'Identité'),
        ('bulletin_paie', 'Bulletin de Paie'),
        ('attestation_travail', 'Attestation de Travail'),
        ('autre', 'Autre Document')
    ], string='Type de Document', required=True, default='autre')