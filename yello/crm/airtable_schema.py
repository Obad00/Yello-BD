"""Construction des payloads API Meta Airtable depuis crm_schema.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "config" / "crm_schema.json"
SEGMENTS_PATH = ROOT / "config" / "segments.json"

# Types créés en dernier (dépendances)
DEFERRED_TYPES = {"formula"}

# Non créables via API Meta — à ajouter dans l'UI Airtable (2 clics chacun)
MANUAL_ONLY_TYPES = {"autoNumber", "createdTime", "lastModifiedTime"}

# Ordre de création : Nom en premier (champ primaire obligatoire)
PRIMARY_FIELD = "Nom"


def load_schema() -> dict[str, Any]:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_segments() -> list[str]:
    with open(SEGMENTS_PATH, encoding="utf-8") as f:
        return json.load(f)["segments"]


def _select_choices(options: list[str]) -> dict[str, Any]:
    return {"choices": [{"name": opt} for opt in options]}


def build_field_payload(field_def: dict[str, Any], segments: list[str]) -> dict[str, Any]:
    """Convertit une entrée du schéma en payload API Airtable."""
    name = field_def["name"]
    ftype = field_def["type"]
    payload: dict[str, Any] = {"name": name, "type": ftype}

    if ftype in ("singleLineText", "email", "phoneNumber", "url", "multilineText"):
        return payload

    if ftype == "number":
        precision = field_def.get("precision", 0)
        payload["options"] = {"precision": precision}
        return payload

    if ftype == "singleSelect":
        if field_def.get("options_ref"):
            opts = segments
        else:
            opts = field_def.get("options", [])
        payload["options"] = _select_choices(opts)
        return payload

    if ftype == "multipleSelects":
        opts = field_def.get("options", [])
        payload["options"] = _select_choices(opts)
        return payload

    if ftype == "checkbox":
        payload["options"] = {"color": "greenBright", "icon": "check"}
        return payload

    if ftype == "date":
        payload["options"] = {"dateFormat": {"name": "iso"}}
        return payload

    if ftype == "formula":
        payload["options"] = {"formula": field_def["formula"]}
        return payload

    if ftype == "autoNumber":
        return payload

    if ftype == "createdTime":
        payload["options"] = {
            "result": {
                "type": "dateTime",
                "options": {
                    "dateFormat": {"name": "local"},
                    "timeFormat": {"name": "24hour"},
                    "timeZone": "client",
                },
            }
        }
        return payload

    if ftype == "lastModifiedTime":
        payload["options"] = {
            "result": {
                "type": "dateTime",
                "options": {
                    "dateFormat": {"name": "local"},
                    "timeFormat": {"name": "24hour"},
                    "timeZone": "client",
                },
            }
        }
        return payload

    raise ValueError(f"Type de champ non supporté : {ftype} ({name})")


def ordered_fields_for_creation(
    schema: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Retourne (champs_immédiats, champs_différés).
    Le premier champ immédiat est toujours Nom (primaire).
    """
    schema = schema or load_schema()
    segments = load_segments()
    immediate: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []

    field_defs = schema["fields"]
    # Réordonner : Nom en premier
    sorted_defs = sorted(
        field_defs,
        key=lambda f: (0 if f["name"] == PRIMARY_FIELD else 1, field_defs.index(f)),
    )

    for fd in sorted_defs:
        if fd["type"] in MANUAL_ONLY_TYPES:
            continue  # voir MANUAL_FIELDS_NOTE dans create_airtable_crm.py
        if fd["type"] in DEFERRED_TYPES:
            deferred.append(build_field_payload(fd, segments))
        else:
            immediate.append(build_field_payload(fd, segments))

    # Nom doit être le premier
    immediate.sort(key=lambda f: 0 if f["name"] == PRIMARY_FIELD else 1)
    return immediate, deferred


def all_field_names(schema: dict[str, Any] | None = None) -> list[str]:
    schema = schema or load_schema()
    return [f["name"] for f in schema["fields"]]


def manual_only_field_names(schema: dict[str, Any] | None = None) -> list[str]:
    schema = schema or load_schema()
    return [f["name"] for f in schema["fields"] if f["type"] in MANUAL_ONLY_TYPES]


MANUAL_FIELDS_NOTE = """
Champs à ajouter manuellement dans Airtable (l'API ne les supporte pas) :
  • ID Contact        → type « Automatic number »
  • Date de création  → type « Created time »
  • Date de mise à jour → type « Last modified time »
"""
