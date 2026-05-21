"""Extraction de contacts professionnels depuis les emails."""

from __future__ import annotations

import re
from email.utils import parseaddr
from typing import Any


# Patterns courants dans les signatures
PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{2,4}(?:\s*(?:ext|poste)\s*\d+)?",
    re.IGNORECASE,
)
LINKEDIN_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/in/[\w%-]+", re.I)
ROLE_LINE_RE = re.compile(
    r"^(?:directeur|directrice|responsable|drh|ceo|fondateur|fondatrice|manager|head|"
    r"président|présidente|formateur|professeur|chargé|chargée).+",
    re.I | re.M,
)
ORG_LINE_RE = re.compile(
    r"^(?:[A-Z][\w\s&.'-]{2,60}(?:SARL|SAS|SA|Ltd|GmbH|Inc|Corp|Université|École|School|ONG|Incubateur)?\.?)$",
    re.M,
)

NOISE_SENDERS = re.compile(
    r"(noreply|no-reply|donotreply|newsletter|notification|mailer-daemon|"
    r"support@|billing@|invoice@|facture@|automated|system@)",
    re.I,
)


def parse_from_header(from_str: str) -> tuple[str, str, str]:
    """Retourne (nom_complet, prenom, email)."""
    name, addr = parseaddr(from_str)
    name = name.strip().strip('"')
    email = addr.strip().lower()
    prenom, nom = "", name
    if name:
        parts = name.split()
        if len(parts) >= 2:
            prenom, nom = parts[0], " ".join(parts[1:])
        elif len(parts) == 1:
            prenom, nom = parts[0], ""
    return name, prenom, email


def extract_phones(text: str) -> list[str]:
    found = []
    for m in PHONE_RE.finditer(text):
        p = re.sub(r"\s+", " ", m.group().strip())
        digits = re.sub(r"\D", "", p)
        if 8 <= len(digits) <= 15:
            found.append(p)
    return list(dict.fromkeys(found))


def extract_linkedin(text: str) -> str:
    m = LINKEDIN_RE.search(text)
    return m.group(0) if m else ""


def extract_signature_block(body: str) -> str:
    """Isole la signature (souvent après -- ou les 15 dernières lignes)."""
    if not body:
        return ""
    markers = ["-- \n", "--\n", "___", "Cordialement", "Bien cordialement", "Best regards", "Kind regards"]
    for marker in markers:
        idx = body.rfind(marker)
        if idx != -1:
            return body[idx:].strip()
    lines = body.strip().splitlines()
    if len(lines) > 20:
        return "\n".join(lines[-15:])
    return body[-1500:] if len(body) > 1500 else body


def extract_organisation_and_role(signature: str) -> tuple[str, str]:
    org, role = "", ""
    lines = [ln.strip() for ln in signature.splitlines() if ln.strip()]
    for ln in lines[:12]:
        if LINKEDIN_RE.search(ln) or PHONE_RE.search(ln) or "@" in ln:
            continue
        if not role and ROLE_LINE_RE.match(ln):
            role = ln[:120]
            continue
        if not org and 3 <= len(ln) <= 80 and not ln.startswith("http"):
            if re.search(r"[A-Za-z]{3,}", ln):
                org = ln[:120]
    return org, role


def should_skip_sender(email: str, from_str: str) -> bool:
    if not email:
        return True
    if NOISE_SENDERS.search(email) or NOISE_SENDERS.search(from_str):
        return True
    return False


def parse_email_to_contact(email_data: dict[str, str]) -> dict[str, Any] | None:
    """
    Transforme un email extrait en contact professionnel.
    Retourne None si l'email doit être ignoré.
    """
    from_str = email_data.get("de", "")
    name, prenom, addr = parse_from_header(from_str)

    if should_skip_sender(addr, from_str):
        return None

    body = email_data.get("corps", "")
    signature = extract_signature_block(body)
    phones = extract_phones(signature + "\n" + body[:500])
    org, poste = extract_organisation_and_role(signature)
    linkedin = extract_linkedin(signature + body)

    return {
        "nom": name.split()[-1] if name and " " in name else (name or ""),
        "prenom": prenom,
        "email": addr,
        "telephone": phones[0] if phones else "",
        "organisation": org,
        "poste": poste,
        "linkedin": linkedin,
        "sujet": email_data.get("sujet", ""),
        "signature": signature[:500],
        "message_id": email_data.get("id", ""),
        "date_email": email_data.get("date", ""),
        "from_raw": from_str,
    }
