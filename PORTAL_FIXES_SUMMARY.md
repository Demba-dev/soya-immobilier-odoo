# Résumé des Corrections du Portail SOYA

## Problèmes Identifiés et Résolus

### 1. **Erreur dans portal_ticket.py**
**Problème**: Le champ `contract_id` référençait `'soya.base.contract'` au lieu du modèle enfant spécifique
**Solution**: Changé à `'soya.rental.contract'` qui est le modèle utilisé dans les données de démo
**Fichier**: `custom_addons/soya_estate/models/portal_ticket.py` (ligne 28)

### 2. **Utilisateurs Portals sans Mot de Passe**
**Problème**: Les mots de passe ne peuvent pas être définis directement via XML
**Solution**: Supprimé les champs `password` du fichier XML et fourni un script SQL pour configurer les mots de passe
**Fichiers**:
- `custom_addons/soya_estate/demo/portal_demo.xml` (lignes 28, 38)
- Créé: `setup_portal_passwords.sql`

### 3. **Structure Incorrecte des Contrats de Location**
**Problème**: Les contrats de location utilisent proto-héritage (`_inherits`) et nécessitent d'abord un enregistrement `soya.base.contract`
**Solution**: 
- Créé d'abord un `soya.base.contract` dans les données de démo
- Puis le `soya.rental.contract` le référence via `base_contract_id`
**Fichier**: `custom_addons/soya_estate/demo/portal_demo.xml` (lignes 66-83)

### 4. **Données de Démo Simplifiées**
**Problème**: Le paiement référençait un contrat au lieu d'une facture
**Solution**: Supprimé le paiement de démo (complexe et non essentiel pour tester le portail)
**Fichier**: `custom_addons/soya_estate/demo/portal_demo.xml`

## Données de Démo Finales

Après redémarrage du serveur, les données suivantes seront créées:

### Utilisateurs
- **proprietaire** / (voir setup_portal_passwords.sql)
  - Email: proprietaire@demo.com
  - Groupe: Portal
  
- **locataire** / (voir setup_portal_passwords.sql)
  - Email: locataire@demo.com
  - Groupe: Portal

### Partenaires
- Jean Dupont (Propriétaire)
- Marie Martin (Locataire)

### Bien Immobilier
- Appartement 3 Chambres - Badalabougou Portal
- Propriétaire: Jean Dupont
- État: Loué

### Contrats
- Contrat de Base: BC-PORTAL-2025-001 (2025-01-15 à 2026-01-15)
- Contrat de Location: Location 3 mois (750,000 FCFA/mois)

### Documents
- Contrat de Location PDF

### Tickets de Support
- 1 ticket ouvert: "Problème d'électricité dans la cuisine" (créé par locataire)

## Prochaines Étapes

### 1. Redémarrer le Serveur
```bash
cd /home/demba/dev/odoo_apps/soya-immobilier-odoo
docker-compose restart web
```

### 2. Configurer les Mots de Passe

**Option A: Via SQL (Recommandé pour les tests)**
```bash
docker-compose exec db psql -U odoo -d soya_odoo_db < setup_portal_passwords.sql
```

**Option B: Via l'Interface Odoo**
1. Connectez-vous avec admin/admin
2. Allez à Settings → Users & Companies → Users
3. Sélectionnez "Propriétaire SOYA" puis "Locataire SOYA"
4. Définissez les mots de passe via le formulaire

### 3. Tester le Portail
- Propriétaire: `http://localhost:8069/my/properties`
- Locataire: `http://localhost:8069/my/rentals`

## Fichiers Modifiés

| Fichier | Modification |
|---------|------------|
| `models/portal_ticket.py` | Changé contract_id de soya.base.contract à soya.rental.contract |
| `demo/portal_demo.xml` | Supprimé passwords, corrigé structure contrats, supprimé paiements |
| **Créés** | |
| `SETUP_PORTAL.md` | Guide de configuration complet |
| `setup_portal_passwords.sql` | Script SQL pour configurer les mots de passe |
| `PORTAL_FIXES_SUMMARY.md` | Ce fichier |

## Validation

Pour vérifier que les données de démo se sont chargées correctement:

```bash
# Connectez-vous à la base de données
docker-compose exec db psql -U odoo -d soya_odoo_db

# Vérifiez les utilisateurs
SELECT login, name, active FROM res_users WHERE login IN ('proprietaire', 'locataire');

# Vérifiez les contrats
SELECT name, id FROM soya_base_contract LIMIT 5;

# Vérifiez les tickets
SELECT subject, state FROM soya_portal_ticket;
```

## Statut Final

✅ Portal controller prêt
✅ Portal ticket model corrigé
✅ Données de démo restructurées
✅ Documentation complète
✅ Scripts de configuration fournis

Le portail est maintenant prêt pour le déploiement et les tests!
