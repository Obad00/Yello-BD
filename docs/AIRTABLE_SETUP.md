# Configuration CRM Airtable — Yello

## Création automatique (recommandé)

### 1. Token Airtable avec les bons droits

Sur [airtable.com/create/tokens](https://airtable.com/create/tokens), créez un token avec :

- `data.records:read` et `data.records:write` (sync contacts)
- **`schema.bases:read`** et **`schema.bases:write`** (création table/champs)

Accès : votre base Yello uniquement.

### 2. Configurer `.env`

```env
AIRTABLE_API_KEY=pat...
AIRTABLE_BASE_ID=appXXXXXXXX    # uniquement l'ID app, pas l'URL complète
AIRTABLE_TABLE_CONTACTS=Contacts
```

### 3. Lancer le script de création

```bash
# Aperçu sans modification
python3 scripts/create_airtable_crm.py --dry-run

# Création réelle (table + tous les champs)
python3 scripts/create_airtable_crm.py
```

Le script :

- crée la table **Contacts** si elle n'existe pas ;
- ajoute tous les champs manquants si la table existe déjà ;
- crée en dernier la formule **Classification score** (dépend de **Score du lead**).

### 4. Champs système (manuel, 1 min)

L'API Airtable **ne permet pas** de créer ces 3 champs — ajoutez-les dans l'interface :

| Champ | Type Airtable (UI) |
|-------|-------------------|
| ID Contact | Automatic number |
| Date de création | Created time |
| Date de mise à jour | Last modified time |

### 5. Vérifier

```bash
python3 scripts/verify_airtable.py
```

---

## Création manuelle (alternative)

### Étape 1 — Créer la base

1. Connectez-vous à [Airtable](https://airtable.com)
2. Créez une base **« Yello CRM »**

### Étape 2 — Créer les champs à la main

Liste des champs (si le script automatique échoue) :

### Champs texte / contact
| Champ | Type Airtable |
|-------|---------------|
| Nom | Single line text |
| Prénom | Single line text |
| Email | Email |
| Téléphone | Phone |
| WhatsApp | Phone |
| LinkedIn | URL |
| Organisation | Single line text |
| Poste | Single line text |
| Pays | Single line text |
| Ville | Single line text |
| Prochaine action | Single line text |
| Commentaires | Long text |
| Sujet discussion | Single line text |

### Listes déroulantes

**Source :** Gmail, Instagram, Facebook, WhatsApp, LinkedIn, Site web, Newsletter, Calendly, Manuel, Autre

**Segment :** Apprenant, Parent, Professeur, Formateur, École, Université, Entreprise, Incubateur, ONG, Institution publique, Investisseur, Partenaire stratégique, Média, Non classé

**Statut commercial :** Nouveau lead, À qualifier, Qualifié, Contacté, RDV proposé, RDV confirmé, Proposition envoyée, Négociation, Converti, Perdu, À relancer plus tard

**Tags contexte :** incubateur, entreprise, école, investisseur, partenaire, média, professionnel

### Champs calculés / système

| Champ | Type | Détail |
|-------|------|--------|
| Score du lead | Number (entier) | 0-100 |
| Classification score | Formula | `IF({Score du lead}>=81,'Priorité commerciale',IF({Score du lead}>=61,'Lead chaud',IF({Score du lead}>=31,'Lead tiède','Lead froid')))` |
| Consentement newsletter | Checkbox | Obligatoire avant envoi Brevo |
| Date de création | Created time | Auto |
| Date de mise à jour | Last modified time | Auto |
| Dernier contact | Date | |

## Étape 3 — Créer les vues

1. **Tous les contacts** — Grid, tri par Date de mise à jour ↓
2. **Leads chauds (61+)** — Filtre : Score du lead ≥ 61
3. **Priorité commerciale** — Filtre : Score du lead ≥ 81
4. **À relancer** — Filtre : Statut = « À relancer plus tard »
5. **Par segment** — Kanban, groupe par Segment
6. **Pipeline commercial** — Kanban, groupe par Statut commercial

## Étape 4 — Token API

1. [Airtable tokens](https://airtable.com/create/tokens)
2. Scopes : `data.records:read`, `data.records:write`
3. Accès : base Yello CRM uniquement
4. Copiez dans `.env` :
   ```
   AIRTABLE_API_KEY=pat...
   AIRTABLE_BASE_ID=app...  # depuis l'URL Airtable
   AIRTABLE_TABLE_CONTACTS=Contacts
   ```

## Étape 5 — Test

```bash
python scripts/sync_gmail_crm.py --dry-run --limite 5
python scripts/sync_gmail_crm.py --limite 5
```

Vérifiez que les contacts apparaissent dans Airtable avec score et segment.

## Interface Airtable (dashboard rapide)

Créez une **Interface** avec :
- KPI : nombre de contacts, leads chauds, convertis
- Graphique : contacts par Source
- Kanban : Pipeline commercial
