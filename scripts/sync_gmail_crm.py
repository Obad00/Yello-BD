#!/usr/bin/env python3
"""Synchronise Gmail → CRM Airtable."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from yello.sync.gmail_to_crm import sync_gmail_to_crm


def main():
    parser = argparse.ArgumentParser(description="Sync Gmail → CRM Yello")
    parser.add_argument("--dossier", default="INBOX", help="Dossier IMAP Gmail")
    parser.add_argument("--critere", default="ALL", help="Critère IMAP (ALL, UNSEEN, etc.)")
    parser.add_argument("--limite", type=int, default=50, help="Nombre max d'emails")
    parser.add_argument("--openai", action="store_true", help="Classification IA OpenAI")
    parser.add_argument("--dry-run", action="store_true", help="Sans écriture CRM")
    parser.add_argument(
        "--export",
        type=Path,
        default=ROOT / "data" / "contacts_export.json",
        help="Chemin export JSON",
    )
    args = parser.parse_args()

    print("╔══════════════════════════════════════╗")
    print("║   Yello — Sync Gmail → CRM           ║")
    print("╚══════════════════════════════════════╝")

    summary = sync_gmail_to_crm(
        dossier=args.dossier,
        critere=args.critere,
        limite=args.limite,
        use_openai=args.openai,
        dry_run=args.dry_run,
        export_json=args.export,
    )

    print(f"\n📧 Contacts analysés : {len(summary['contacts'])}")
    if not args.dry_run and not summary.get("errors"):
        print(f"✅ Créés : {summary.get('created', 0)}")
        print(f"🔄 Mis à jour : {summary.get('updated', 0)}")
    if summary.get("dry_run"):
        print("ℹ️  Mode dry-run — aucune écriture CRM")
    if summary.get("errors"):
        for err in summary["errors"]:
            print(f"⚠️  {err}")
    print(f"💾 Export → {args.export}")


if __name__ == "__main__":
    main()
