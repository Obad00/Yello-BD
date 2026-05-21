# Guide d'utilisation — Équipe Yello

## 1. Première configuration (une fois)

1. Créez la base Airtable selon `docs/AIRTABLE_SETUP.md`
2. Copiez `.env.example` → `.env` et remplissez :
   - `GMAIL_ADDRESS` + `GMAIL_APP_PASSWORD`
   - `AIRTABLE_API_KEY` + `AIRTABLE_BASE_ID`
3. (Optionnel) Ajoutez `OPENAI_API_KEY` pour classification IA et contenus

## 2. Synchroniser les emails en contacts CRM

```bash
python scripts/sync_gmail_crm.py --limite 50
```

**Résultat :** les emails professionnels deviennent des contacts dans Airtable avec segment et score.

**Mode test :**
```bash
python scripts/sync_gmail_crm.py --dry-run --limite 10
```
Les contacts sont exportés dans `data/contacts_export.json` sans toucher au CRM.

## 3. Comprendre le score d'un lead

| Critère | Points |
|---------|--------|
| Email professionnel | +10 |
| Téléphone | +10 |
| Poste décisionnaire | +20 |
| Organisation identifiée | +15 |
| RDV pris | +25 |
| Ouverture newsletter | +5 |
| Clic lien | +10 |

Consultez les leads chauds dans Airtable : vue **« Leads chauds (61+) »**.

## 4. Réseaux sociaux (Instagram, WhatsApp, etc.)

1. Configurez ManyChat ou GoHighLevel avec les réponses de `templates/social/auto_replies.json`
2. Pointez le webhook vers votre n8n : workflow `n8n/social-lead-webhook.json`
3. Chaque message qualifié crée un contact dans Airtable

## 5. Newsletter (tous les 15 jours)

1. Créez les listes Brevo par segment
2. Cochez **Consentement newsletter** dans Airtable pour chaque contact
3. Importez `n8n/newsletter-brevo-sync.json` dans n8n
4. Planifiez l'envoi des campagnes dans Brevo

## 6. Générer du contenu pour LinkedIn / réseaux

```bash
python scripts/generate_content.py "Comment l'IA aide les profs" -t linkedin -s Professeur
```

Types disponibles : `linkedin`, `instagram`, `facebook`, `email`, `carousel`, `video_script`

**Toujours valider** le contenu avant publication (exigence CDC).

## 7. Prospection LinkedIn

- Séquences prêtes : `templates/linkedin/sequences.json`
- Messages personnalisés IA :
```python
from yello.ai.openai_classifier import generate_linkedin_message
msg = generate_linkedin_message(contact, step="presentation")
```

## 8. Prise de rendez-vous

Remplacez `calendly_url` dans `templates/social/auto_replies.json` par votre lien Calendly réel.

Les leads avec score ≥ 61 reçoivent automatiquement une alerte (workflow n8n).

## 9. Tableau de bord

Suivez les KPI dans Airtable Interface ou Looker Studio — voir `docs/DASHBOARD_KPI.md`.

## Dépannage

| Problème | Solution |
|----------|----------|
| Erreur connexion Gmail | Vérifiez le mot de passe d'application (16 car.) |
| Airtable inaccessible | Vérifiez `AIRTABLE_API_KEY` et noms de champs |
| Aucun contact extrait | Les emails noreply/newsletter sont filtrés volontairement |
| OpenAI ne répond pas | Vérifiez `OPENAI_API_KEY` ou utilisez sans `--openai` |
