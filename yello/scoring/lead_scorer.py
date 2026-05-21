"""Scoring des leads Yello (0-100) selon le cahier des charges."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "scoring_rules.json"


def load_scoring_config() -> dict[str, Any]:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def is_professional_email(email: str, personal_domains: list[str] | None = None) -> bool:
    if not email or "@" not in email:
        return False
    domain = email.split("@")[-1].lower().strip()
    config = load_scoring_config()
    blocked = set(personal_domains or config.get("personal_email_domains", []))
    return domain not in blocked


def is_decision_maker_role(poste: str) -> bool:
    if not poste:
        return False
    config = load_scoring_config()
    poste_lower = poste.lower()
    for kw in config.get("criteria", []):
        if kw.get("id") == "decision_maker_role":
            return any(k in poste_lower for k in kw.get("keywords", []))
    return False


def classify_score(score: int) -> str:
    config = load_scoring_config()
    c = config["classification"]
    if score >= c["priority"]["min"]:
        return c["priority"]["label"]
    if score >= c["hot"]["min"]:
        return c["hot"]["label"]
    if score >= c["warm"]["min"]:
        return c["warm"]["label"]
    return c["cold"]["label"]


def compute_score(
    *,
    email: str = "",
    telephone: str = "",
    poste: str = "",
    organisation: str = "",
    positive_response: bool = False,
    meeting_booked: bool = False,
    newsletter_opened: bool = False,
    link_clicked: bool = False,
    no_response_after_3_followups: bool = False,
) -> int:
    """Calcule le score sur 100 selon les critères du CDC."""
    config = load_scoring_config()
    points_map = {c["id"]: c["points"] for c in config["criteria"]}
    score = 0

    if is_professional_email(email):
        score += points_map.get("professional_email", 10)
    if telephone and len(telephone.replace(" ", "")) >= 8:
        score += points_map.get("phone_available", 10)
    if is_decision_maker_role(poste):
        score += points_map.get("decision_maker_role", 20)
    if organisation and len(organisation.strip()) >= 2:
        score += points_map.get("organization_identified", 15)
    if positive_response:
        score += points_map.get("positive_response", 20)
    if meeting_booked:
        score += points_map.get("meeting_booked", 25)
    if newsletter_opened:
        score += points_map.get("newsletter_opened", 5)
    if link_clicked:
        score += points_map.get("link_clicked", 10)
    if no_response_after_3_followups:
        score += points_map.get("no_response_3_followups", -20)

    max_s = config.get("max_score", 100)
    min_s = config.get("min_score", 0)
    return max(min_s, min(max_s, score))


def score_contact_dict(contact: dict[str, Any]) -> dict[str, Any]:
    """Enrichit un dict contact avec score et classification."""
    s = compute_score(
        email=contact.get("email", ""),
        telephone=contact.get("telephone", ""),
        poste=contact.get("poste", ""),
        organisation=contact.get("organisation", ""),
        positive_response=contact.get("positive_response", False),
        meeting_booked=contact.get("meeting_booked", False),
        newsletter_opened=contact.get("newsletter_opened", False),
        link_clicked=contact.get("link_clicked", False),
        no_response_after_3_followups=contact.get("no_response_after_3_followups", False),
    )
    contact["score"] = s
    contact["classification"] = classify_score(s)
    return contact
