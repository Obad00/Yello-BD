# Architecture technique Yello

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                    SOURCES DE LEADS                              │
│  Instagram │ Facebook │ WhatsApp │ LinkedIn │ Gmail │ Site     │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              COUCHE CAPTURE & AUTOMATISATION                   │
│  ManyChat/GHL (webhook) │ Script Python Gmail │ n8n workflows   │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TRAITEMENT YELLO (Python)                     │
│  Parse contact → Classify segment → Score 0-100 → Dedup email   │
│  [Optionnel] OpenAI enrichment                                   │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CRM — AIRTABLE                                │
│  Contacts │ Segments │ Statuts │ Score │ Tags │ Consentement    │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   ┌─────────┐         ┌──────────┐         ┌─────────────┐
   │  Brevo  │         │ Calendly │         │  Dashboard  │
   │Newsletter│        │   RDV    │         │ Looker/Airtable│
   └─────────┘         └──────────┘         └─────────────┘
```

## Stack retenue (no-code + code)

| Composant | Outil | Rôle |
|-----------|-------|------|
| Automatisation | n8n | Orchestration, webhooks, planification |
| CRM | Airtable | Base centralisée |
| Gmail | Python IMAP | Extraction contacts pro |
| IA | OpenAI API | Classification, contenus, messages LinkedIn |
| Newsletter | Brevo | Envoi bi-mensuel |
| RDV | Calendly | Liens dans réponses auto |
| Messages sociaux | ManyChat / GHL | À connecter via webhook |
| Dashboard | Airtable Interface / Looker Studio | KPI |

## Flux prioritaires (CDC)

### Priorité 1 — CRM
- Schéma : `config/crm_schema.json`
- Client : `yello/crm/airtable_client.py`
- Setup : `scripts/setup_airtable.py`

### Priorité 2 — Réseaux sociaux
- Templates : `templates/social/auto_replies.json`
- Webhook n8n : `n8n/social-lead-webhook.json`

### Priorité 3 — Gmail
- Pipeline : `yello/sync/gmail_to_crm.py`
- CLI : `scripts/sync_gmail_crm.py`

### Priorité 4 — Newsletter
- Config segments : `templates/newsletter/segments.json`
- Workflow : `n8n/newsletter-brevo-sync.json`

### Priorité 5 — LinkedIn
- Séquences : `templates/linkedin/sequences.json`
- Génération IA : `yello/ai/openai_classifier.py`

### Priorité 6 — Reporting
- Voir `docs/DASHBOARD_KPI.md`

## Scoring (règles métier)

Config : `config/scoring_rules.json`

| Score | Classification |
|-------|----------------|
| 0-30 | Lead froid |
| 31-60 | Lead tiède |
| 61-80 | Lead chaud |
| 81-100 | Priorité commerciale |

## Sécurité

- Credentials dans `.env` (jamais commité)
- Consentement newsletter obligatoire avant sync Brevo
- Validation humaine avant campagnes massives
- Logs via exports JSON dans `data/`

## Évolution vers stack avancée

Le package `yello/` peut migrer vers Node.js/Python + PostgreSQL en remplaçant uniquement `yello/crm/airtable_client.py` par un adaptateur PostgreSQL/HubSpot.
