#!/usr/bin/env python3
"""
Crée automatiquement la table CRM « Contacts » et tous ses champs dans Airtable
via l'API Meta (schema.bases:write).

Usage:
  python3 scripts/create_airtable_crm.py
  python3 scripts/create_airtable_crm.py --dry-run
  python3 scripts/create_airtable_crm.py --force-rename-old  # renomme l'ancienne table si conflit
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from yello.crm.airtable_schema import (
    load_schema,
    ordered_fields_for_creation,
    all_field_names,
    manual_only_field_names,
    MANUAL_FIELDS_NOTE,
)

try:
    import requests
except ImportError:
    print("❌ Installez requests : pip install requests")
    sys.exit(1)

API_BASE = "https://api.airtable.com/v0/meta/bases"
DELAY_SEC = 0.25  # respecter les limites API


class AirtableSchemaClient:
    def __init__(self, api_key: str, base_id: str):
        self.base_id = base_id.strip()
        if "/" in self.base_id:
            self.base_id = self.base_id.split("/")[0]
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def _url(self, path: str) -> str:
        return f"{API_BASE}/{self.base_id}{path}"

    def list_tables(self) -> list[dict]:
        r = self.session.get(self._url("/tables"), timeout=30)
        if r.status_code == 403:
            raise PermissionError(
                "Token refusé. Ajoutez les scopes schema.bases:read et schema.bases:write "
                "sur https://airtable.com/create/tokens"
            )
        r.raise_for_status()
        return r.json().get("tables", [])

    def create_table(self, name: str, fields: list[dict], description: str = "") -> dict:
        body: dict = {"name": name, "fields": fields}
        if description:
            body["description"] = description
        r = self.session.post(self._url("/tables"), json=body, timeout=60)
        if not r.ok:
            raise RuntimeError(f"Création table échouée ({r.status_code}): {r.text}")
        return r.json()

    def create_field(self, table_id: str, field: dict) -> dict:
        r = self.session.post(
            self._url(f"/tables/{table_id}/fields"),
            json=field,
            timeout=30,
        )
        if not r.ok:
            raise RuntimeError(
                f"Champ « {field.get('name')} » ({r.status_code}): {r.text}"
            )
        return r.json()

    def rename_table(self, table_id: str, new_name: str) -> None:
        r = self.session.patch(
            self._url(f"/tables/{table_id}"),
            json={"name": new_name},
            timeout=30,
        )
        if not r.ok:
            print(f"⚠️  Renommage table ignoré : {r.text[:200]}")


def find_table(tables: list[dict], name: str) -> dict | None:
    for t in tables:
        if t.get("name") == name:
            return t
    return None


def existing_field_names(table: dict) -> set[str]:
    return {f["name"] for f in table.get("fields", [])}


def create_missing_fields(
    client: AirtableSchemaClient,
    table_id: str,
    fields: list[dict],
    existing: set[str],
    dry_run: bool,
) -> list[str]:
    created = []
    for field in fields:
        name = field["name"]
        if name in existing:
            print(f"  ⏭  {name} — déjà présent")
            continue
        if dry_run:
            print(f"  ➕ {name} [{field['type']}] — serait créé")
            created.append(name)
            continue
        try:
            client.create_field(table_id, field)
            print(f"  ✅ {name} [{field['type']}]")
            created.append(name)
            time.sleep(DELAY_SEC)
        except RuntimeError as e:
            print(f"  ❌ {name} — {e}")
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description="Créer le CRM Airtable Yello")
    parser.add_argument("--dry-run", action="store_true", help="Afficher sans créer")
    parser.add_argument(
        "--force-rename-old",
        action="store_true",
        help="Renomme une table Contacts existante en Contacts_old",
    )
    args = parser.parse_args()

    api_key = os.getenv("AIRTABLE_API_KEY", "")
    base_id = os.getenv("AIRTABLE_BASE_ID", "")
    table_name = os.getenv("AIRTABLE_TABLE_CONTACTS", "Contacts")

    print("╔══════════════════════════════════════════════╗")
    print("║   Yello — Création CRM Airtable (API)        ║")
    print("╚══════════════════════════════════════════════╝\n")

    if not api_key:
        print("❌ AIRTABLE_API_KEY manquant dans .env")
        return 1
    if not base_id:
        print("❌ AIRTABLE_BASE_ID manquant dans .env")
        return 1

    schema = load_schema()
    immediate, deferred = ordered_fields_for_creation(schema)
    description = schema.get("description", "CRM Yello")

    print(f"Base   : {base_id.split('/')[0]}")
    print(f"Table  : {table_name}")
    print(f"Champs : {len(all_field_names())} au total")
    if args.dry_run:
        print("Mode   : DRY-RUN (aucune modification)\n")
    else:
        print()

    client = AirtableSchemaClient(api_key, base_id)

    try:
        tables = client.list_tables()
    except PermissionError as e:
        print(f"❌ {e}")
        return 1
    except requests.RequestException as e:
        print(f"❌ Connexion Airtable : {e}")
        return 1

    table = find_table(tables, table_name)

    if table is None:
        # Créer la table avec les champs immédiats (max ~20 par requête initiale)
        # Airtable exige au moins 1 champ ; on envoie les champs simples d'abord
        initial_batch = immediate[:15]
        remaining_immediate = immediate[15:]

        print(f"📦 Création de la table « {table_name} » avec {len(initial_batch)} champs…")
        if args.dry_run:
            for f in initial_batch + remaining_immediate + deferred:
                print(f"  ➕ {f['name']} [{f['type']}]")
            print("\n✅ Dry-run terminé.")
            return 0

        try:
            table = client.create_table(table_name, initial_batch, description)
            table_id = table["id"]
            print(f"✅ Table créée (id: {table_id})")
            existing = existing_field_names(table)
        except RuntimeError as e:
            print(f"❌ {e}")
            return 1

        time.sleep(DELAY_SEC)
        create_missing_fields(client, table_id, remaining_immediate, existing, False)
        existing = existing | set(f["name"] for f in initial_batch + remaining_immediate)
        create_missing_fields(client, table_id, deferred, existing, False)

    else:
        table_id = table["id"]
        existing = existing_field_names(table)
        print(f"📋 Table « {table_name} » existe (id: {table_id}) — {len(existing)} champ(s)\n")

        # Si la table par défaut n'a qu'un champ « Name » / « Nom » vide, on complète
        all_to_add = immediate + deferred
        # Exclure champs déjà là (y compris variantes Airtable par défaut)
        print("Ajout des champs manquants :\n")
        created = create_missing_fields(
            client, table_id, all_to_add, existing, args.dry_run
        )
        if not args.dry_run:
            print(f"\n✅ {len(created)} champ(s) ajouté(s).")
        else:
            print(f"\n✅ {len(created)} champ(s) seraient ajoutés.")

    if not args.dry_run:
        print("\n🔍 Vérification…")
        tables = client.list_tables()
        table = find_table(tables, table_name)
        if table:
            names = existing_field_names(table)
            expected = set(all_field_names())
            manual = set(manual_only_field_names())
            missing = expected - names - manual
            missing_manual = manual - names
            if missing:
                print(f"⚠️  Champs API manquants : {', '.join(sorted(missing))}")
                print("   Relancez le script.")
            elif missing_manual:
                print("✅ Tous les champs API sont présents.")
                print(MANUAL_FIELDS_NOTE)
            else:
                print("✅ Tous les champs du schéma sont présents.")
        print("\n🎉 Prochaine étape :")
        print("   python3 scripts/verify_airtable.py")
        print("   python3 scripts/sync_gmail_crm.py --dry-run --limite 10")

    return 0


if __name__ == "__main__":
    sys.exit(main())
