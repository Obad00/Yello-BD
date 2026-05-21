# Conformité RGPD & bonnes pratiques — Yello

Checklist issue du cahier des charges (section 8).

## Consentement & communication

- [ ] **Consentement newsletter** : case « Consentement newsletter » cochée dans Airtable avant tout envoi Brevo
- [ ] **Double opt-in** recommandé pour Brevo (confirmation email)
- [ ] **Désabonnement** : lien obligatoire dans chaque newsletter (géré par Brevo)
- [ ] **Messages sociaux** : mentionner l'utilisation des données dans la politique de confidentialité Yello

## Protection des données

- [ ] Credentials uniquement dans `.env` (fichier dans `.gitignore`)
- [ ] Accès Airtable limité par token (scopes minimaux)
- [ ] Accès restreint à l'équipe Yello (pas de partage public des bases)
- [ ] **Sauvegarde** : export Airtable hebdomadaire (planifié dans n8n ou manuel)

## Traitement automatisé

- [ ] **Logs** : exports JSON datés dans `data/` pour traçabilité des sync Gmail
- [ ] **Filtrage** : emails noreply/newsletter/personnels non pertinents exclus (`contact_parser.py`)
- [ ] **Dédoublonnage** : upsert par email dans `airtable_client.py`
- [ ] **Validation humaine** avant toute campagne massive (processus équipe)
- [ ] **Suppression** : procédure de droit à l'effacement (supprimer ligne Airtable + Brevo)

## Anti-spam

- [ ] Respecter les limites LinkedIn (séquences semi-auto, pas de spam)
- [ ] Pas d'envoi massif sans consentement
- [ ] Relances max 3 avant pénalité score (-20 points)

## Registre des traitements (à compléter par Yello)

| Traitement | Base légale | Durée conservation |
|------------|-------------|-------------------|
| CRM contacts | Intérêt légitime / consentement | 3 ans inactivité |
| Newsletter | Consentement | Jusqu'au désabonnement |
| Messages sociaux | Exécution demande utilisateur | 2 ans |

## Actions techniques implémentées

1. Champ `Consentement newsletter` dans le schéma CRM
2. Filtre Brevo n8n : `Consentement newsletter = TRUE`
3. Exclusion domaines webmail pour scoring (pas pour stockage si contact pro explicite)
4. Pas de commit des fichiers `.env` ou exports sensibles

## Contact DPO

À désigner par Yello pour répondre aux demandes RGPD (accès, rectification, suppression).
