"""
Yello CRM — Création automatique de la base Airtable
=====================================================
Ce script crée la base "Yello CRM" avec tous les champs,
segments, statuts et options définis dans le cahier des charges.

Prérequis :
    pip install requests

Configuration :
    1. Va sur https://airtable.com/create/tokens
    2. Crée un token avec les scopes :
       - schema.bases:write
       - data.records:write
    3. Copie ton token dans AIRTABLE_TOKEN ci-dessous
    4. Copie l'ID de ton workspace dans WORKSPACE_ID
       (visible dans l'URL : airtable.com/[workspaceId]/...)

Utilisation :
    python create_yello_crm.py
"""

import requests
import json
import sys

# ─────────────────────────────────────────────
# CONFIGURATION — à remplir avant de lancer
# ─────────────────────────────────────────────
import os

AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
WORKSPACE_ID   = "wspsFEvySvnpcMFrA"   # ex: wspABCD1234EFGH5678
# ─────────────────────────────────────────────

BASE_URL = "https://api.airtable.com/v0/meta"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json",
}


# ── Couleurs des statuts commerciaux ──────────────────────────────────────────
STATUT_OPTIONS = [
    {"name": "Nouveau lead",          "color": "blueLight2"},
    {"name": "À qualifier",           "color": "cyanLight2"},
    {"name": "Qualifié",              "color": "tealLight2"},
    {"name": "Contacté",              "color": "greenLight2"},
    {"name": "RDV proposé",           "color": "yellowLight2"},
    {"name": "RDV confirmé",          "color": "orangeLight2"},
    {"name": "Proposition envoyée",   "color": "pinkLight2"},
    {"name": "Négociation",           "color": "purpleLight2"},
    {"name": "Converti",              "color": "greenDark1"},
    {"name": "Perdu",                 "color": "redDark1"},
    {"name": "À relancer plus tard",  "color": "grayLight2"},
]

# ── Couleurs des segments ──────────────────────────────────────────────────────
SEGMENT_OPTIONS = [
    {"name": "Apprenant",             "color": "blueLight2"},
    {"name": "Parent",                "color": "cyanLight2"},
    {"name": "Professeur",            "color": "tealLight2"},
    {"name": "Formateur",             "color": "greenLight2"},
    {"name": "École",                 "color": "yellowLight2"},
    {"name": "Université",            "color": "orangeLight2"},
    {"name": "Entreprise",            "color": "pinkLight2"},
    {"name": "Incubateur",            "color": "purpleLight2"},
    {"name": "ONG",                   "color": "grayLight2"},
    {"name": "Institution publique",  "color": "blueLight1"},
    {"name": "Investisseur",          "color": "redLight2"},
    {"name": "Partenaire stratégique","color": "orangeDark1"},
    {"name": "Média",                 "color": "pinkDark1"},
]

# ── Sources ────────────────────────────────────────────────────────────────────
SOURCE_OPTIONS = [
    {"name": "Gmail",       "color": "redLight2"},
    {"name": "Instagram",   "color": "pinkLight2"},
    {"name": "Facebook",    "color": "blueLight2"},
    {"name": "WhatsApp",    "color": "greenLight2"},
    {"name": "LinkedIn",    "color": "cyanLight2"},
    {"name": "Site web",    "color": "purpleLight2"},
    {"name": "Referral",    "color": "yellowLight2"},
    {"name": "Manuel",      "color": "grayLight2"},
]

# ── Définition complète des champs ────────────────────────────────────────────
FIELDS = [
    # Identité
    {
        "name": "Nom",
        "type": "singleLineText",
        "description": "Nom de famille du contact",
    },
    {
        "name": "Prénom",
        "type": "singleLineText",
        "description": "Prénom du contact",
    },
    {
        "name": "Email",
        "type": "email",
        "description": "Email principal — clé de déduplication (doit être unique)",
    },
    {
        "name": "Téléphone",
        "type": "phoneNumber",
        "description": "Numéro de téléphone principal",
    },
    {
        "name": "WhatsApp",
        "type": "phoneNumber",
        "description": "Numéro WhatsApp (si différent du téléphone)",
    },
    {
        "name": "LinkedIn",
        "type": "url",
        "description": "URL du profil LinkedIn",
    },

    # Organisation
    {
        "name": "Organisation",
        "type": "singleLineText",
        "description": "Nom de l'entreprise, école ou institution",
    },
    {
        "name": "Poste",
        "type": "singleLineText",
        "description": "Titre ou fonction du contact",
    },
    {
        "name": "Pays",
        "type": "singleLineText",
        "description": "Pays de résidence ou de l'organisation",
    },
    {
        "name": "Ville",
        "type": "singleLineText",
        "description": "Ville de résidence ou de l'organisation",
    },

    # Qualification
    {
        "name": "Source",
        "type": "singleSelect",
        "options": {"choices": SOURCE_OPTIONS},
        "description": "Canal d'acquisition du contact",
    },
    {
        "name": "Segment",
        "type": "singleSelect",
        "options": {"choices": SEGMENT_OPTIONS},
        "description": "Catégorie du contact selon le cahier des charges Yello",
    },
    {
        "name": "Statut commercial",
        "type": "singleSelect",
        "options": {"choices": STATUT_OPTIONS},
        "description": "Étape du contact dans le pipeline commercial",
    },
    {
        "name": "Score du lead",
        "type": "number",
        "options": {"precision": 0},
        "description": "Score de 0 à 100. Calcul : email pro +10, tél +10, poste déc. +20, org +15, réponse +20, RDV +25, ouverture +5, clic +10, 3 relances sans réponse -20",
    },
    {
        "name": "Dernier contact",
        "type": "date",
        "options": {"dateFormat": {"name": "european"}},
        "description": "Date du dernier échange avec ce contact",
    },
    {
        "name": "Prochaine action",
        "type": "singleLineText",
        "description": "Prochaine étape à faire pour ce contact (ex: Relance J+5, Envoyer proposition)",
    },
    {
        "name": "Objet email",
        "type": "singleLineText",
        "description": "Sujet du dernier email échangé — rempli automatiquement par n8n",
    },
    {
        "name": "Commentaires",
        "type": "multilineText",
        "description": "Notes libres sur le contact, contexte, historique des échanges",
    },
]


def validate_config():
    """Vérifie que le token et le workspace sont configurés."""
    if AIRTABLE_TOKEN.startswith("patXXX"):
        print("❌ Erreur : configure ton AIRTABLE_TOKEN avant de lancer le script.")
        print("   → https://airtable.com/create/tokens")
        sys.exit(1)
    if WORKSPACE_ID.startswith("wspXXX"):
        print("❌ Erreur : configure ton WORKSPACE_ID avant de lancer le script.")
        print("   → Visible dans l'URL de ton workspace sur airtable.com")
        sys.exit(1)


def create_base():
    """Crée la base Yello CRM dans le workspace."""
    print("📦 Création de la base 'Yello CRM'...")

    # La première table est créée avec la base.
    # Les champs sont ajoutés ensuite un par un.
    payload = {
        "name": "Yello CRM",
        "workspaceId": WORKSPACE_ID,
        "tables": [
            {
                "name": "Contacts",
                "description": "Base de données contacts Yello — leads, clients, partenaires, investisseurs",
                "fields": [
                    {"name": "Nom", "type": "singleLineText"},
                ],
            }
        ],
    }

    resp = requests.post(
        f"{BASE_URL}/bases",
        headers=HEADERS,
        json=payload,
    )

    if resp.status_code != 200:
        print(f"❌ Erreur création base : {resp.status_code}")
        print(resp.text)
        sys.exit(1)

    data = resp.json()
    base_id  = data["id"]
    table_id = data["tables"][0]["id"]

    print(f"✅ Base créée : {base_id}")
    print(f"   Table Contacts : {table_id}")
    return base_id, table_id


def add_fields(base_id, table_id):
    """Ajoute tous les champs à la table Contacts."""
    print(f"\n📋 Ajout de {len(FIELDS)} champs...")

    url = f"{BASE_URL}/bases/{base_id}/tables/{table_id}/fields"
    errors = []

    for field in FIELDS:
        # "Nom" est déjà créé avec la base, on le saute
        if field["name"] == "Nom":
            print(f"   ⏭  Nom (déjà créé avec la base)")
            continue

        payload = {"name": field["name"], "type": field["type"]}

        if "options" in field:
            payload["options"] = field["options"]
        if "description" in field:
            payload["description"] = field["description"]

        resp = requests.post(url, headers=HEADERS, json=payload)

        if resp.status_code == 200:
            print(f"   ✅ {field['name']}")
        else:
            err = f"   ❌ {field['name']} : {resp.status_code} — {resp.text}"
            print(err)
            errors.append(err)

    return errors


def add_sample_record(base_id, table_id):
    """Ajoute un contact exemple pour valider la structure."""
    print("\n👤 Ajout d'un contact exemple...")

    url = f"https://api.airtable.com/v0/{base_id}/Contacts"

    record = {
        "fields": {
            "Nom": "Dabo",
            "Prénom": "Adama",
            "Email": "adama@yello.africa",
            "Organisation": "Yello",
            "Poste": "Fondateur",
            "Pays": "Sénégal",
            "Ville": "Dakar",
            "Source": "Manuel",
            "Segment": "Partenaire stratégique",
            "Statut commercial": "Qualifié",
            "Score du lead": 55,
            "Prochaine action": "Valider le CRM et lancer Phase 2",
            "Commentaires": "Contact créé automatiquement lors de la création de la base.",
        }
    }

    resp = requests.post(url, headers=HEADERS, json={"records": [record]})

    if resp.status_code == 200:
        record_id = resp.json()["records"][0]["id"]
        print(f"   ✅ Contact exemple créé : {record_id}")
    else:
        print(f"   ⚠️  Contact exemple non créé : {resp.status_code}")
        print(f"   {resp.text}")


def print_summary(base_id, errors):
    """Affiche le résumé final avec les liens utiles."""
    print("\n" + "═" * 55)
    print("🎉 Yello CRM créé avec succès !")
    print("═" * 55)
    print(f"\n🔗 Ouvre ta base ici :")
    print(f"   https://airtable.com/{base_id}")
    print(f"\n📌 Note ton Base ID (utile pour n8n) :")
    print(f"   {base_id}")
    print(f"\n📋 Prochaines étapes :")
    print(f"   1. Ouvre la base et vérifie les champs")
    print(f"   2. Ajoute le champ Email comme clé unique (manuellement dans Airtable)")
    print(f"   3. Crée les vues : Pipeline, Leads chauds, À relancer")
    print(f"   4. Configure le workflow n8n Gmail → Airtable")

    if errors:
        print(f"\n⚠️  {len(errors)} champ(s) non créé(s) :")
        for e in errors:
            print(f"   {e}")
        print(f"\n   → Ces champs peuvent être ajoutés manuellement dans Airtable.")

    print("\n" + "═" * 55)


def main():
    print("═" * 55)
    print("  Yello CRM — Création Airtable automatique")
    print("═" * 55 + "\n")

    validate_config()

    base_id, table_id = create_base()
    errors = add_fields(base_id, table_id)
    add_sample_record(base_id, table_id)
    print_summary(base_id, errors)


if __name__ == "__main__":
    main()
