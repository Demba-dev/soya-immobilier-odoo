# Guide de Configuration du Portail SOYA

## Redémarrage du Serveur avec Données de Démo

Pour charger les données de démo du portail, redémarrez le serveur Docker:

```bash
cd /home/demba/dev/odoo_apps/soya-immobilier-odoo
docker-compose restart web
```

Attendez 30-60 secondes pour que le serveur soit prêt, puis accédez à: `http://localhost:8069`

## Configuration des Utilisateurs Portals

Après le redémarrage du serveur, les utilisateurs portals sont créés mais sans mot de passe. Vous avez deux options:

### Option 1: Configurer les mots de passe via SQL (Recommandé pour les tests)

Accédez à la base de données et exécutez ces commandes:

```sql
-- Génère les mots de passe pour les utilisateurs de démo
UPDATE res_users SET password = 'proprietaire123' WHERE login = 'proprietaire';
UPDATE res_users SET password = 'locataire123' WHERE login = 'locataire';
```

### Option 2: Utiliser l'interface Odoo (Processus normal)

1. Connectez-vous en tant qu'administrateur (login: `admin`, password: `admin`)
2. Allez à: **Paramètres → Utilisateurs et Sociétés → Utilisateurs**
3. Sélectionnez l'utilisateur "Propriétaire SOYA"
4. Cliquez sur le bouton **"Envoyer une invitation"** (ou définissez manuellement le mot de passe en éditant l'enregistrement)
5. Répétez pour l'utilisateur "Locataire SOYA"

## Identifiants de Connexion pour les Tests

### Utilisateur Propriétaire
- **Login**: `proprietaire`
- **Mot de passe**: `proprietaire123`
- **Rôle**: Propriétaire de bien immobilier
- **Accès**: Tableau de bord propriétaire (`/my/properties`)

### Utilisateur Locataire
- **Login**: `locataire`
- **Mot de passe**: `locataire123`
- **Rôle**: Locataire
- **Accès**: Tableau de bord locataire (`/my/rentals`)

## Données de Démo Créées

### Bien Immobilier
- **Nom**: Appartement 3 Chambres - Badalabougou Portal
- **Propriétaire**: Jean Dupont
- **Loyer**: 750,000 FCFA/mois
- **Caution**: 2,250,000 FCFA
- **État**: Loué

### Contrat de Location
- **Durée**: 15 janvier 2025 - 15 janvier 2026 (12 mois)
- **Locataire**: Marie Martin
- **Loyer**: 750,000 FCFA/mois

### Documents
- **Contrat de Location** - Accessible aux deux parties

### Paiements
- **Paiement Effectué**: 750,000 FCFA le 20 janvier 2025

### Ticket de Support
- **Sujet**: Problème d'électricité dans la cuisine
- **Catégorie**: Problème Technique
- **Priorité**: Haute
- **Créateur**: Marie Martin (Locataire)

## Accès aux Fonctionnalités du Portail

### Pour le Propriétaire (`proprietaire`)
1. Accédez à: `http://localhost:8069/my/properties`
2. Consultez:
   - Liste de vos biens immobiliers
   - Détails de chaque bien (locataire actuel, loyer, revenus)
   - Documents associés
   - Historique des paiements

### Pour le Locataire (`locataire`)
1. Accédez à: `http://localhost:8069/my/rentals`
2. Consultez:
   - Contrats de location actifs
   - Détails du contrat (dates, montants, durée)
   - Documents du contrat (télécharger)
   - Historique des paiements (12 derniers mois)

### Documents en Ligne
- **Route**: `http://localhost:8069/my/documents`
- Accès centralisé à tous les documents
- Téléchargement sécurisé avec vérification des permissions

### Communication Digitale
- **Route**: `http://localhost:8069/my/messages`
- Créer un nouveau ticket de support
- Consulter l'historique des tickets
- Répondre aux tickets ouverts

## Gestion des Tickets de Support (Backoffice)

Les administrateurs et staff peuvent gérer les tickets via:
**SOYA → Tickets de Support**

Actions disponibles:
- Consulter tous les tickets
- Assigner un ticket à un agent
- Changer l'état (Ouvert → En Cours → Résolu → Fermé)
- Répondre via le Chatter intégré

## Vérification de la Structure des Données

Pour vérifier que les données de démo sont bien chargées:

```bash
# Vérifier les utilisateurs portals
curl -X GET http://localhost:8069/web/dataset/search_read \
  -H "Content-Type: application/json" \
  -d '{"model":"res.users","fields":["login","name","groups_id"],"domain":[["login","in",["proprietaire","locataire"]]]}'

# Vérifier les contrats de location
curl -X GET http://localhost:8069/web/dataset/search_read \
  -H "Content-Type: application/json" \
  -d '{"model":"soya.rental.contract","fields":["name","tenant_id","monthly_rent"]}'
```

## Troubleshooting

### Les utilisateurs portals ne se connectent pas
1. Vérifiez que les mots de passe sont configurés (voir Option 1 ci-dessus)
2. Assurez-vous que les utilisateurs sont actifs (`active = True`)
3. Vérifiez que le groupe `base.group_portal` est assigné

### Les documents ne s'affichent pas
1. Vérifiez que le contrat de location est créé
2. Assurez-vous que le document est attaché au contrat
3. Vérifiez les permissions d'accès

### Les routes du portail retournent des erreurs 404
1. Assurez-vous que le module `portal` est installé
2. Vérifiez que le contrôleur `portal.py` est chargé correctement
3. Consultez les logs du serveur Odoo

## Logs du Serveur

Pour consulter les logs en temps réel:

```bash
docker-compose logs -f web
```

Pour rechercher des erreurs spécifiques:

```bash
docker-compose logs web | grep "ERROR\|Warning\|portal"
```
