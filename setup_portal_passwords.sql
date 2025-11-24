-- Script de Configuration des Mots de Passe du Portail SOYA
-- Exécutez ce script dans PostgreSQL pour configurer les mots de passe des utilisateurs de démo

-- Configuration des mots de passe pour les utilisateurs portals
UPDATE res_users 
SET password = 'proprietaire123' 
WHERE login = 'proprietaire' AND active = true;

UPDATE res_users 
SET password = 'locataire123' 
WHERE login = 'locataire' AND active = true;

-- Vérification: Affiche les utilisateurs portals créés
SELECT id, name, login, email, active 
FROM res_users 
WHERE login IN ('proprietaire', 'locataire');

-- Note: Les commandes UPDATE ci-dessus définissent directement les mots de passe.
-- En production, préférez utiliser le processus d'invitation via l'interface Odoo.
