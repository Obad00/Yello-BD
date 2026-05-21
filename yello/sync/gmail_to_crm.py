"""Pipeline Gmail → parsing → scoring → CRM Airtable."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from yello.gmail.extractor import fetch_and_parse_contacts
from yello.ai.openai_classifier import classify_with_openai


def load_env() -> None:
    root = Path(__file__).resolve().parents[2]
    env_path = root / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def sync_gmail_to_crm(
    *,
    dossier: str = "INBOX",
    critere: str = "ALL",
    limite: int = 50,
    use_openai: bool = False,
    dry_run: bool = False,
    export_json: Path | None = None,
) -> dict[str, Any]:
    """
    Synchronise les contacts Gmail vers Airtable.
    Retourne un résumé {created, updated, skipped, errors, contacts}.
    """
    load_env()

    email_addr = os.getenv("GMAIL_ADDRESS", "")
    app_pass = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")

    if not email_addr or not app_pass:
        raise ValueError("GMAIL_ADDRESS et GMAIL_APP_PASSWORD requis dans .env")

    contacts = fetch_and_parse_contacts(
        email_addr,
        app_pass,
        dossier=dossier,
        critere=critere,
        limite=limite,
    )

    if use_openai and os.getenv("OPENAI_API_KEY"):
        contacts = [classify_with_openai(c) for c in contacts]

    summary: dict[str, Any] = {
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "errors": [],
        "contacts": contacts,
        "timestamp": datetime.now().isoformat(),
    }

    if export_json:
        export_json.parent.mkdir(parents=True, exist_ok=True)
        with open(export_json, "w", encoding="utf-8") as f:
            json.dump(contacts, f, ensure_ascii=False, indent=2)

    if dry_run:
        summary["dry_run"] = True
        return summary

    try:
        from yello.crm.airtable_client import AirtableCRM
        crm = AirtableCRM()
    except (ImportError, ValueError) as e:
        summary["errors"].append(str(e))
        summary["message"] = "Export JSON uniquement — configurez Airtable dans .env"
        return summary

    for c in contacts:
        try:
            result = crm.upsert_from_dict(c)
            if result["action"] == "created":
                summary["created"] += 1
            else:
                summary["updated"] += 1
        except Exception as ex:
            summary["errors"].append(f"{c.get('email')}: {ex}")

    return summary
