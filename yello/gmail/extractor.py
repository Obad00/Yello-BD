"""Extraction Gmail via IMAP — module réutilisable."""

from __future__ import annotations

import email
import imaplib
from email.header import decode_header
from pathlib import Path
from typing import Any


IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993


def decode_str(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            charset = charset or "utf-8"
            try:
                result.append(part.decode(charset, errors="replace"))
            except (LookupError, UnicodeDecodeError):
                result.append(part.decode("utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def extract_body(msg: email.message.Message) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = part.get("Content-Disposition", "")
            if ct == "text/plain" and "attachment" not in cd:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                body = payload.decode(charset, errors="replace") if payload else ""
                break
            if ct == "text/html" and "attachment" not in cd and not body:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                body = payload.decode(charset, errors="replace") if payload else ""
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="replace")
    return body.strip()


def parse_email(raw_data: bytes) -> dict[str, str]:
    msg = email.message_from_bytes(raw_data)
    return {
        "id": msg.get("Message-ID", ""),
        "de": decode_str(msg.get("From", "")),
        "a": decode_str(msg.get("To", "")),
        "cc": decode_str(msg.get("Cc", "")),
        "sujet": decode_str(msg.get("Subject", "")),
        "date": decode_str(msg.get("Date", "")),
        "corps": extract_body(msg),
    }


def connect(email_address: str, app_password: str) -> imaplib.IMAP4_SSL:
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(email_address, app_password.replace(" ", ""))
    return mail


def fetch_emails(
    mail: imaplib.IMAP4_SSL,
    dossier: str = "INBOX",
    critere: str = "ALL",
    limite: int | None = None,
) -> list[dict[str, str]]:
    status, _ = mail.select(f'"{dossier}"', readonly=True)
    if status != "OK":
        return []

    status, data = mail.search(None, critere)
    if status != "OK":
        return []

    ids = data[0].split()
    if limite:
        ids = ids[-limite:]

    emails = []
    for eid in ids:
        status, msg_data = mail.fetch(eid, "(RFC822)")
        if status == "OK" and msg_data and msg_data[0]:
            raw = msg_data[0][1]
            if isinstance(raw, bytes):
                emails.append(parse_email(raw))
    return emails


def fetch_and_parse_contacts(
    email_address: str,
    app_password: str,
    *,
    dossier: str = "INBOX",
    critere: str = "ALL",
    limite: int | None = 50,
) -> list[dict[str, Any]]:
    """Extrait les emails et retourne les contacts professionnels parsés."""
    from yello.gmail.contact_parser import parse_email_to_contact
    from yello.gmail.classifier import enrich_contact
    from yello.scoring.lead_scorer import score_contact_dict

    mail = connect(email_address, app_password)
    try:
        raw_emails = fetch_emails(mail, dossier=dossier, critere=critere, limite=limite)
    finally:
        mail.logout()

    contacts = []
    seen_emails: set[str] = set()

    for em in raw_emails:
        parsed = parse_email_to_contact(em)
        if not parsed or not parsed.get("email"):
            continue
        email_key = parsed["email"].lower()
        if email_key in seen_emails:
            continue
        seen_emails.add(email_key)
        enrich_contact(parsed)
        score_contact_dict(parsed)
        contacts.append(parsed)

    return contacts
