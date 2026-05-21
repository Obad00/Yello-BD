# Yello — Système d'automatisation commerciale

Implémentation du **cahier des charges technique** Yello : CRM, Gmail, scoring, contenus, workflows n8n et documentation.

## Structure du projet

```
├── config/              # Schéma CRM, segments, règles de scoring
├── yello/               # Package Python principal
│   ├── gmail/           # Extraction + parsing contacts
│   ├── crm/             # Client Airtable
│   ├── scoring/         # Score leads 0-100
│   ├── ai/              # Classification OpenAI (optionnel)
│   └── sync/            # Pipeline Gmail → CRM
├── scripts/             # CLI : sync, scoring, contenu, setup Airtable
├── n8n/                 # Workflows importables (Gmail, Brevo, réseaux sociaux)
├── templates/           # Séquences LinkedIn, réponses sociales, newsletter
├── docs/                # Architecture, guides, RGPD, KPI
├── gmail_extractor/     # Extracteur email standalone (legacy)
└── tests/               # Tests scoring
```

## Démarrage rapide

### 1. Prérequis

- Python 3.10+
- Compte Gmail avec [mot de passe d'application](https://myaccount.google.com/apppasswords)
- (Optionnel) Compte Airtable + clé API
- (Optionnel) Clé OpenAI

### 2. Installation

```bash
cd /home/meblo-barham/Bureau/Projet/teste
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Éditez .env avec vos identifiants
```

### 3. Configurer le CRM Airtable (automatique)

```bash
python3 scripts/create_airtable_crm.py --dry-run   # aperçu
python3 scripts/create_airtable_crm.py             # création table + champs
python3 scripts/verify_airtable.py
```

### 4. Synchroniser Gmail → CRM

```bash
# Test sans écriture CRM
python scripts/sync_gmail_crm.py --dry-run --limite 20

# Sync réelle vers Airtable
python scripts/sync_gmail_crm.py --limite 50

# Avec classification IA
python scripts/sync_gmail_crm.py --openai --limite 30
```

### 5. Générer du contenu

```bash
python scripts/generate_content.py "L'IA dans les écoles primaires" -t linkedin -s École
```

### 6. Importer les workflows n8n

Fichiers dans `n8n/` → import dans votre instance n8n.

## Modules livrés vs CDC

| Module CDC | Statut | Fichiers |
|------------|--------|----------|
| CRM centralisé | ✅ Schéma + client Python | `config/crm_schema.json`, `yello/crm/` |
| Gmail extraction | ✅ Complet | `yello/gmail/`, `scripts/sync_gmail_crm.py` |
| Scoring leads | ✅ Complet | `yello/scoring/`, `config/scoring_rules.json` |
| Newsletter | ✅ Templates + workflow n8n | `templates/newsletter/`, `n8n/newsletter-brevo-sync.json` |
| LinkedIn | ✅ Séquences + générateur IA | `templates/linkedin/`, `yello/ai/` |
| Réseaux sociaux | ✅ Templates réponses | `templates/social/`, `n8n/social-lead-webhook.json` |
| Contenu fondateur | ✅ Script génération | `scripts/generate_content.py` |
| Reporting KPI | ✅ Doc dashboard | `docs/DASHBOARD_KPI.md` |
| Conformité RGPD | ✅ Checklist | `docs/CONFORMITE_RGPD.md` |

## Ce qui nécessite vos comptes externes

- **ManyChat / GoHighLevel** → connecter au webhook `n8n/social-lead-webhook.json`
- **Brevo** → clé API + listes dans `.env`
- **Calendly** → liens dans `templates/social/auto_replies.json`
- **PhantomBuster / Clay** → prospection LinkedIn (hors code)

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Guide d'utilisation](docs/GUIDE_UTILISATION.md)
- [Configuration Airtable](docs/AIRTABLE_SETUP.md)
- [Dashboard KPI](docs/DASHBOARD_KPI.md)
- [Conformité RGPD](docs/CONFORMITE_RGPD.md)

## Tests

```bash
python tests/test_scoring.py
```
