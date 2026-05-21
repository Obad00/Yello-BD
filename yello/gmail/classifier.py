"""Classification des contacts par segment (règles + mots-clés)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CONFIG = Path(__file__).resolve().parents[2] / "config" / "segments.json"

CONTEXT_TAGS = {
    "incubateur": ["incubateur", "incubator", "accelerator"],
    "entreprise": ["entreprise", "company", "sarl", "sas", "startup"],
    "école": ["école", "school", "lycée", "collège", "université", "university"],
    "investisseur": ["investisseur", "investor", "vc", "venture", "capital"],
    "partenaire": ["partenaire", "partner", "partnership"],
    "média": ["média", "media", "journal", "presse", "rédaction"],
}


def load_segments_config() -> dict[str, Any]:
    with open(_CONFIG, encoding="utf-8") as f:
        return json.load(f)


def classify_segment(contact: dict[str, Any]) -> str:
    """Détermine le segment à partir du contenu email/signature."""
    config = load_segments_config()
    keywords_map: dict[str, list[str]] = config.get("classification_keywords", {})

    haystack = " ".join(
        filter(
            None,
            [
                contact.get("poste", ""),
                contact.get("organisation", ""),
                contact.get("sujet", ""),
                contact.get("signature", ""),
                contact.get("from_raw", ""),
            ],
        )
    ).lower()

    best_segment = "Non classé"
    best_hits = 0

    for segment, keywords in keywords_map.items():
        hits = sum(1 for kw in keywords if kw.lower() in haystack)
        if hits > best_hits:
            best_hits = hits
            best_segment = segment

    return best_segment


def extract_context_tags(contact: dict[str, Any]) -> list[str]:
    haystack = " ".join(
        [
            contact.get("organisation", ""),
            contact.get("poste", ""),
            contact.get("sujet", ""),
            contact.get("signature", ""),
        ]
    ).lower()
    tags = []
    for tag, keywords in CONTEXT_TAGS.items():
        if any(kw in haystack for kw in keywords):
            tags.append(tag)
    if not tags and contact.get("email"):
        from yello.scoring.lead_scorer import is_professional_email
        if is_professional_email(contact["email"]):
            tags.append("professionnel")
    return tags


def enrich_contact(contact: dict[str, Any]) -> dict[str, Any]:
    contact["segment"] = classify_segment(contact)
    contact["tags"] = extract_context_tags(contact)
    return contact
