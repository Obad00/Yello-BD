# 📬 Gmail Email Extractor

Programme Python pour extraire et exporter les emails d'une boîte Gmail.

> **Nouveau :** Pour le pipeline complet (parsing contacts, scoring, sync CRM), utilisez le package principal à la racine du projet :
> ```bash
> python scripts/sync_gmail_crm.py --dry-run
> ```
> Voir le [README principal](../README.md).

## ✅ Prérequis

- Python 3.10+
- Aucune bibliothèque externe requise (utilise uniquement la bibliothèque standard)

## 🔐 Obtenir un Mot de passe d'application Google

> ⚠️ N'utilisez **jamais** votre mot de passe Gmail habituel dans un script !

1. Connectez-vous à votre compte Google
2. Allez sur **Sécurité** → https://myaccount.google.com/security
3. Activez la **Validation en deux étapes** (obligatoire)
4. Cherchez **"Mots de passe des applications"** → https://myaccount.google.com/apppasswords
5. Sélectionnez **Mail** → **Autre appareil** → nommez-le (ex: "Script Python")
6. Copiez le code de **16 caractères** généré — c'est votre mot de passe d'application

## 🚀 Utilisation

```bash
cd gmail_extractor
python gmail_extractor.py
```

Le programme vous demandera :
1. Votre adresse Gmail
2. Votre mot de passe d'application (16 caractères)
3. Le dossier à lire (INBOX, Envoyés, Spam…)
4. Un critère de recherche (tous, non lus, par expéditeur, par mot-clé…)
5. Un nombre limite d'emails (optionnel)
6. Le format d'export (CSV, JSON, TXT ou tous)

## 📂 Fichiers exportés

Les fichiers sont sauvegardés dans le dossier `emails_exportes/` :

| Format | Description |
|--------|-------------|
| `.csv` | Ouvrable avec Excel / LibreOffice Calc |
| `.json` | Idéal pour traitement programmatique |
| `.txt` | Texte lisible, un email par bloc |

## 🔍 Exemples de critères de recherche IMAP

| Critère | Description |
|---------|-------------|
| `ALL` | Tous les emails |
| `UNSEEN` | Emails non lus |
| `FROM "alice@gmail.com"` | D'un expéditeur précis |
| `SUBJECT "facture"` | Contenant "facture" dans le sujet |
| `SINCE 01-Jan-2024` | Depuis une date |
| `BEFORE 01-Jan-2024` | Avant une date |
| `SEEN` | Emails déjà lus |

## 📁 Dossiers Gmail courants

| Nom IMAP | Description |
|----------|-------------|
| `INBOX` | Boîte de réception |
| `[Gmail]/Sent Mail` | Emails envoyés |
| `[Gmail]/Spam` | Courrier indésirable |
| `[Gmail]/All Mail` | Tous les emails |
| `[Gmail]/Drafts` | Brouillons |
| `[Gmail]/Trash` | Corbeille |
