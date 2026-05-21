#!/usr/bin/env python3
"""Vérifie la connexion Airtable et liste les champs de la table Contacts."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def main():
    api_key = os.getenv("AIRTABLE_API_KEY", "")
    base_id = os.getenv("AIRTABLE_BASE_ID", "")
    table_name = os.getenv("AIRTABLE_TABLE_CONTACTS", "Contacts")

    print("╔══════════════════════════════════════╗")
    print("║   Vérification Airtable Yello        ║")
    print("╚══════════════════════════════════════╝\n")

    if not api_key:
        print("❌ AIRTABLE_API_KEY manquant dans .env")
        return 1
    if not base_id or "/" in base_id:
        print("❌ AIRTABLE_BASE_ID invalide.")
        print("   Utilisez uniquement l'ID commençant par app…")
        print("   Exemple URL : https://airtable.com/appXXXX/...")
        print("   → AIRTABLE_BASE_ID=appXXXX")
        return 1

    print(f"✓ Base ID : {base_id}")
    print(f"✓ Table   : {table_name}\n")

    try:
        import requests
    except ImportError:
        requests = None

    # Meta API — schéma de la base
    if requests:
        url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
        headers = {"Authorization": f"Bearer {api_key}"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 403:
            print("⚠️  Token sans accès Meta API (schema.bases:read).")
            print("   Ajoutez ce scope sur https://airtable.com/create/tokens")
            print("   → Test des enregistrements uniquement…\n")
        elif r.status_code == 200:
            tables = r.json().get("tables", [])
            names = [t["name"] for t in tables]
            print(f"✅ Connexion OK — {len(tables)} table(s) : {', '.join(names)}")
            for t in tables:
                if t["name"] == table_name:
                    fields = [f["name"] for f in t.get("fields", [])]
                    print(f"\n📋 Champs dans « {table_name} » ({len(fields)}) :")
                    for f in fields:
                        print(f"   • {f}")
                    missing = _missing_fields(fields)
                    if missing:
                        print(f"\n⚠️  Champs manquants ({len(missing)}) — à créer dans Airtable :")
                        for m in missing:
                            print(f"   • {m}")
                    else:
                        print("\n✅ Tous les champs requis sont présents.")
                    break
            else:
                print(f"\n❌ Table « {table_name} » introuvable.")
                print(f"   Tables disponibles : {names}")
                return 1
        else:
            print(f"⚠️  Meta API : HTTP {r.status_code} — {r.text[:200]}")

    # Test lecture enregistrements
    try:
        from yello.crm.airtable_client import AirtableCRM
        crm = AirtableCRM()
        records = crm.list_all(max_records=3)
        print(f"\n✅ Lecture CRM OK — {len(records)} contact(s) (max 3 affichés)")
        for rec in records:
            f = rec.get("fields", {})
            print(f"   • {f.get('Nom', '?')} — {f.get('Email', 'sans email')}")
    except Exception as e:
        print(f"\n❌ Erreur lecture CRM : {e}")
        return 1

    print("\n🎉 Airtable est prêt. Lancez :")
    print("   python3 scripts/sync_gmail_crm.py --dry-run --limite 10")
    return 0


def _missing_fields(existing: list[str]) -> list[str]:
    required = [
        "Nom", "Prénom", "Email", "Téléphone", "Organisation", "Poste",
        "Source", "Segment", "Statut commercial", "Score du lead",
    ]
    optional_manual = {"ID Contact", "Date de création", "Date de mise à jour"}
    return [r for r in required if r not in existing and r not in optional_manual]


if __name__ == "__main__":
    sys.exit(main() or 0)
