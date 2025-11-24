# Checklist de Déploiement du Portail SOYA

## Phase 1: Préparation

- [ ] Lire le fichier `SETUP_PORTAL.md` pour comprendre la configuration
- [ ] Lire le fichier `PORTAL_FIXES_SUMMARY.md` pour les corrections apportées
- [ ] Sauvegarder la base de données actuelle (backup)

## Phase 2: Redémarrage du Serveur

```bash
cd /home/demba/dev/odoo_apps/soya-immobilier-odoo
docker-compose restart web
```

- [ ] Attendre 30-60 secondes pour que le serveur soit opérationnel
- [ ] Vérifier que le serveur démarre sans erreurs: `docker-compose logs web | grep ERROR`

## Phase 3: Configuration des Utilisateurs Portals

### Option A: Via SQL (Recommandé)

```bash
docker-compose exec db psql -U odoo -d soya_odoo_db < setup_portal_passwords.sql
```

- [ ] Exécuter le script SQL
- [ ] Vérifier que la commande s'est exécutée sans erreurs

### Option B: Via Interface Odoo

1. [ ] Accédez à `http://localhost:8069` (login: admin, password: admin)
2. [ ] Allez à **Settings → Users & Companies → Users**
3. [ ] Trouvez "Propriétaire SOYA"
   - [ ] Cliquez sur "Edit"
   - [ ] Trouvez le champ "Password"
   - [ ] Entrez: `proprietaire123`
   - [ ] Cliquez sur "Save"
4. [ ] Répétez pour "Locataire SOYA" avec `locataire123`

## Phase 4: Vérification des Données

### Via SQL

```bash
docker-compose exec db psql -U odoo -d soya_odoo_db
```

Exécutez ces requêtes:

```sql
-- Vérifier les utilisateurs
SELECT login, name, active, id FROM res_users 
WHERE login IN ('proprietaire', 'locataire');

-- Vérifier les contacts
SELECT name, email FROM res_partner 
WHERE name LIKE '%Demo%' OR name LIKE '%Dupont%' OR name LIKE '%Martin%';

-- Vérifier les propriétés
SELECT name, owner_id FROM soya_property 
WHERE name LIKE '%Badalabougou%';

-- Vérifier les contrats
SELECT name, id FROM soya_base_contract LIMIT 1;

-- Vérifier les contrats de location
SELECT id, tenant_id FROM soya_rental_contract LIMIT 1;

-- Vérifier les tickets de support
SELECT subject, state FROM soya_portal_ticket;
```

- [ ] Tous les enregistrements sont présents
- [ ] Les mots de passe sont définis pour les utilisateurs portals

## Phase 5: Test des Portails

### Test Propriétaire

1. [ ] Accédez à `http://localhost:8069`
2. [ ] **Déconnexion** si connecté en tant qu'admin
3. [ ] **Connexion** avec:
   - Login: `proprietaire`
   - Mot de passe: `proprietaire123`
4. [ ] Vérifier que vous êtes connecté en tant que "Propriétaire SOYA"
5. [ ] Accédez à `http://localhost:8069/my/properties`
6. [ ] [ ] Vérifier que vous voyez la propriété "Appartement 3 Chambres"
7. [ ] Cliquez sur la propriété
8. [ ] [ ] Vérifiez les détails:
   - Locataire: Marie Martin
   - Loyer: 750,000 FCFA
   - Durée: 12 mois
9. [ ] Retournez et consultez les autres sections:
   - [ ] `/my/documents` - Voir le contrat PDF
   - [ ] Backoffice "Tickets de Support" - Voir le ticket créé

### Test Locataire

1. [ ] **Déconnexion** (cliquez sur le profil)
2. [ ] **Connexion** avec:
   - Login: `locataire`
   - Mot de passe: `locataire123`
3. [ ] Vérifier que vous êtes connecté en tant que "Locataire SOYA"
4. [ ] Accédez à `http://localhost:8069/my/rentals`
5. [ ] [ ] Vérifier que vous voyez le contrat:
   - Propriétaire: Jean Dupont
   - Loyer: 750,000 FCFA
   - Durée: 12 mois (du 15/01/2025 au 15/01/2026)
6. [ ] Cliquez sur le contrat
7. [ ] [ ] Vérifiez les détails et le document
8. [ ] Allez à `/my/documents`
9. [ ] [ ] Téléchargez le contrat PDF
10. [ ] Allez à `/my/messages`
11. [ ] [ ] Vérifiez le ticket ouvert
12. [ ] [ ] Essayez de répondre au ticket

## Phase 6: Gestion Backoffice

### Admin: Gestion des Tickets

1. [ ] Connectez-vous avec admin/admin
2. [ ] Allez à **SOYA → Tickets de Support**
3. [ ] [ ] Vérifiez que vous voyez le ticket "Problème d'électricité"
4. [ ] [ ] Testez les actions:
   - [ ] Marquer comme "En Cours"
   - [ ] Assigner à un agent
   - [ ] Ajouter une note via Chatter
   - [ ] Marquer comme "Résolu"
   - [ ] Fermer le ticket

## Phase 7: Résolution des Problèmes

### Les utilisateurs portals ne se connectent pas

- [ ] Vérifiez que les mots de passe sont configurés (voir Phase 3)
- [ ] Vérifiez qu'ils sont actifs: `SELECT active FROM res_users WHERE login='proprietaire'`
- [ ] Vérifiez le groupe portal: `SELECT groups_id FROM res_users WHERE login='proprietaire'`
- [ ] Consultez les logs: `docker-compose logs web | tail -50`

### Les propriétés n'apparaissent pas

- [ ] Vérifiez que la propriété est créée: `SELECT * FROM soya_property WHERE name LIKE '%Badalabougou%'`
- [ ] Vérifiez que owner_id est correct
- [ ] Vérifiez les permissions: `SELECT * FROM ir_model_access WHERE model_id=XXX`

### Les contrats n'apparaissent pas

- [ ] Vérifiez les contrats: `SELECT * FROM soya_rental_contract`
- [ ] Vérifiez que le base_contract_id est présent
- [ ] Vérifiez les permissions

### Les documents ne s'affichent pas

- [ ] Vérifiez: `SELECT * FROM soya_contract_document`
- [ ] Vérifiez le contract_id
- [ ] Essayez de télécharger le document

### Erreurs 404 sur les routes portail

- [ ] Vérifiez que `portal` est installé: `SELECT * FROM ir_module_module WHERE name='portal' AND state='installed'`
- [ ] Vérifiez que portal.py est chargé: `docker-compose logs web | grep -i portal`
- [ ] Redémarrez le serveur

## Phase 8: Nettoyage (Optionnel)

- [ ] Supprimez les données de démo après les tests (si pas nécessaires en production)
- [ ] Archivez les logs de test
- [ ] Documentez tout problème rencontré

## Phase 9: Déploiement en Production

- [ ] [ ] Créer une sauvegarde de la base de données
- [ ] [ ] Tester les scénarios critiques en production
- [ ] [ ] Configurer les mots de passe réels pour les utilisateurs finaux
- [ ] [ ] Mettre à jour la documentation utilisateur
- [ ] [ ] Former les utilisateurs (propriétaires et locataires)

## Notes Importantes

1. **Mots de passe temporaires**: Les mots de passe `proprietaire123` et `locataire123` sont temporaires pour les tests
2. **Données de démo**: Supprimez après les tests si désiré
3. **Backups**: Effectuez des backups réguliers
4. **Logs**: Consultez `docker-compose logs web` en cas de problème
5. **Performance**: Le portail peut être lent si la base de données est volumineuse

## Support

Pour plus d'aide, consultez:
- `SETUP_PORTAL.md` - Guide de configuration complet
- `PORTAL_FIXES_SUMMARY.md` - Détails des corrections
- Logs Odoo: `docker-compose logs web`
- Base de données: `docker-compose exec db psql -U odoo -d soya_odoo_db`
