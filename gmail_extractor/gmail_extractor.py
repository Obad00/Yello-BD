"""
Gmail Email Extractor
=====================
Extrait les emails d'une adresse Gmail via IMAP.
Utilise un "Mot de passe d'application" Google (App Password) pour une connexion sécurisée.

Comment obtenir un Mot de passe d'application :
  1. Allez sur https://myaccount.google.com/security
  2. Activez la "Validation en deux étapes" si ce n'est pas déjà fait
  3. Cherchez "Mots de passe des applications"
  4. Créez un nouveau mot de passe pour "Mail" sur "Autre appareil"
  5. Utilisez ce mot de passe de 16 caractères dans ce script
"""

import imaplib
import email
import email.message
from email.header import decode_header
import csv
import json
import os
import getpass
from datetime import datetime
from pathlib import Path


# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────
IMAP_SERVER   = "imap.gmail.com"
IMAP_PORT     = 993
OUTPUT_DIR    = Path("emails_exportes")


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def decode_str(value) -> str:
    """Décode une chaîne encodée (RFC 2047) en UTF-8 propre."""
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


def extract_body(msg: email.message.Message) -> str:  # type: ignore[name-defined]
    """Extrait le corps texte d'un email (priorité text/plain → text/html)."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = part.get("Content-Disposition", "")
            if ct == "text/plain" and "attachment" not in cd:
                payload = part.get_payload(decode=True)
                charset  = part.get_content_charset() or "utf-8"
                body = payload.decode(charset, errors="replace")
                break
            if ct == "text/html" and "attachment" not in cd and not body:
                payload = part.get_payload(decode=True)
                charset  = part.get_content_charset() or "utf-8"
                body = payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="replace")
    return body.strip()


def parse_email(raw_data: bytes) -> dict:
    """Parse les données brutes d'un email et retourne un dictionnaire."""
    msg = email.message_from_bytes(raw_data)
    return {
        "id"      : msg.get("Message-ID", ""),
        "de"      : decode_str(msg.get("From", "")),
        "a"       : decode_str(msg.get("To", "")),
        "cc"      : decode_str(msg.get("Cc", "")),
        "sujet"   : decode_str(msg.get("Subject", "")),
        "date"    : decode_str(msg.get("Date", "")),
        "corps"   : extract_body(msg),
    }


# ──────────────────────────────────────────────
# CONNEXION GMAIL
# ──────────────────────────────────────────────

def connect(email_address: str, app_password: str) -> imaplib.IMAP4_SSL:
    """Établit la connexion IMAP avec Gmail."""
    print(f"\n🔌 Connexion à Gmail ({IMAP_SERVER}:{IMAP_PORT})...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(email_address, app_password)
    print("✅ Connexion réussie !")
    return mail


def list_folders(mail: imaplib.IMAP4_SSL) -> list[str]:
    """Liste tous les dossiers/labels de la boîte Gmail."""
    status, folders = mail.list()
    result = []
    if status == "OK":
        for folder in folders:
            if isinstance(folder, bytes):
                # Format : (\HasNoChildren) "/" "INBOX"
                parts = folder.decode().split('"')
                if len(parts) >= 3:
                    result.append(parts[-2].strip())
    return result


# ──────────────────────────────────────────────
# EXTRACTION DES EMAILS
# ──────────────────────────────────────────────

def fetch_emails(
    mail          : imaplib.IMAP4_SSL,
    dossier       : str = "INBOX",
    critere       : str = "ALL",
    limite        : int | None = None,
) -> list[dict]:
    """
    Extrait les emails d'un dossier donné.

    Paramètres :
        mail    : connexion IMAP active
        dossier : dossier à lire (ex: "INBOX", "[Gmail]/Sent Mail")
        critere : critère de recherche IMAP (ex: "ALL", "UNSEEN", "FROM someone@email.com")
        limite  : nombre maximum d'emails à récupérer (None = tous)
    """
    print(f"\n📂 Ouverture du dossier : {dossier}")
    status, _ = mail.select(f'"{dossier}"', readonly=True)
    if status != "OK":
        print(f"❌ Impossible d'ouvrir le dossier : {dossier}")
        return []

    print(f"🔍 Recherche avec le critère : {critere}")
    status, data = mail.search(None, critere)
    if status != "OK":
        print("❌ Erreur lors de la recherche.")
        return []

    ids = data[0].split()
    total = len(ids)
    print(f"📧 {total} email(s) trouvé(s).")

    if limite:
        ids = ids[-limite:]  # Prendre les N plus récents
        print(f"⚠️  Extraction limitée aux {len(ids)} plus récents.")

    emails = []
    for i, eid in enumerate(ids, 1):
        print(f"  ↓ Extraction {i}/{len(ids)} (id={eid.decode()})...", end="\r")
        status, msg_data = mail.fetch(eid, "(RFC822)")
        if status == "OK" and msg_data and msg_data[0]:
            raw = msg_data[0][1]
            if isinstance(raw, bytes):
                emails.append(parse_email(raw))

    print(f"\n✅ {len(emails)} email(s) extraits avec succès.")
    return emails


# ──────────────────────────────────────────────
# EXPORT
# ──────────────────────────────────────────────

def save_csv(emails: list[dict], filepath: Path) -> None:
    """Sauvegarde les emails dans un fichier CSV."""
    if not emails:
        return
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=emails[0].keys())
        writer.writeheader()
        writer.writerows(emails)
    print(f"💾 CSV exporté → {filepath}")


def save_json(emails: list[dict], filepath: Path) -> None:
    """Sauvegarde les emails dans un fichier JSON."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(emails, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON exporté → {filepath}")


def save_txt(emails: list[dict], filepath: Path) -> None:
    """Sauvegarde les emails dans un fichier texte lisible."""
    separator = "=" * 70 + "\n"
    with open(filepath, "w", encoding="utf-8") as f:
        for i, e in enumerate(emails, 1):
            f.write(separator)
            f.write(f"EMAIL #{i}\n")
            f.write(separator)
            f.write(f"De      : {e['de']}\n")
            f.write(f"À       : {e['a']}\n")
            f.write(f"Cc      : {e['cc']}\n")
            f.write(f"Sujet   : {e['sujet']}\n")
            f.write(f"Date    : {e['date']}\n")
            f.write(f"\n--- Corps ---\n{e['corps']}\n\n")
    print(f"💾 TXT exporté  → {filepath}")


# ──────────────────────────────────────────────
# MENU INTERACTIF
# ──────────────────────────────────────────────

def afficher_menu_dossiers(dossiers: list[str]) -> str:
    """Affiche la liste des dossiers et demande un choix."""
    print("\n📁 Dossiers disponibles :")
    dossiers_communs = ["INBOX", "[Gmail]/Sent Mail", "[Gmail]/Spam", "[Gmail]/All Mail"]
    affiches = []
    # Mettre les dossiers communs en priorité
    for d in dossiers_communs:
        if d in dossiers:
            affiches.append(d)
    for d in dossiers:
        if d not in affiches:
            affiches.append(d)

    for i, d in enumerate(affiches, 1):
        print(f"  {i:2}. {d}")

    choix = input("\n➤ Numéro du dossier [1 = INBOX] : ").strip()
    try:
        index = int(choix) - 1
        return affiches[index]
    except (ValueError, IndexError):
        return "INBOX"


def afficher_menu_critere() -> str:
    """Demande le critère de recherche IMAP."""
    print("\n🔎 Critère de recherche :")
    print("  1. Tous les emails (ALL)")
    print("  2. Non lus seulement (UNSEEN)")
    print("  3. Emails d'un expéditeur spécifique")
    print("  4. Emails contenant un mot dans le sujet")
    print("  5. Emails reçus aujourd'hui")
    print("  6. Critère personnalisé (IMAP raw)")

    choix = input("\n➤ Votre choix [1] : ").strip() or "1"

    if choix == "1":
        return "ALL"
    elif choix == "2":
        return "UNSEEN"
    elif choix == "3":
        exp = input("   Adresse de l'expéditeur : ").strip()
        return f'FROM "{exp}"'
    elif choix == "4":
        mot = input("   Mot-clé dans le sujet : ").strip()
        return f'SUBJECT "{mot}"'
    elif choix == "5":
        today = datetime.now().strftime("%d-%b-%Y")
        return f'SINCE {today}'
    elif choix == "6":
        return input("   Critère IMAP : ").strip()
    return "ALL"


def afficher_menu_format() -> list[str]:
    """Demande le format d'export."""
    print("\n📤 Format d'export :")
    print("  1. CSV  (tableur)")
    print("  2. JSON (développeurs)")
    print("  3. TXT  (texte lisible)")
    print("  4. Tous les formats")

    choix = input("\n➤ Votre choix [1] : ").strip() or "1"
    mapping = {
        "1": ["csv"],
        "2": ["json"],
        "3": ["txt"],
        "4": ["csv", "json", "txt"],
    }
    return mapping.get(choix, ["csv"])


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    print("╔══════════════════════════════════════════╗")
    print("║      📬  Gmail Email Extractor  📬       ║")
    print("╚══════════════════════════════════════════╝")
    print()
    print("⚠️  Utilisez un 'Mot de passe d'application' Google,")
    print("    PAS votre mot de passe Gmail habituel.")
    print("    → https://myaccount.google.com/apppasswords\n")

    # Identifiants
    email_address = input("📧 Adresse Gmail : ").strip()
    app_password  = getpass.getpass("🔑 Mot de passe d'application (16 car.) : ")

    try:
        mail = connect(email_address, app_password)
    except imaplib.IMAP4.error as e:
        print(f"\n❌ Erreur de connexion : {e}")
        print("   → Vérifiez votre adresse et votre mot de passe d'application.")
        return

    # Lister les dossiers
    dossiers = list_folders(mail)
    dossier  = afficher_menu_dossiers(dossiers)

    # Critère de recherche
    critere = afficher_menu_critere()

    # Limite
    limite_str = input("\n⚙️  Nombre max d'emails à extraire (Entrée = tous) : ").strip()
    limite = int(limite_str) if limite_str.isdigit() else None

    # Format d'export
    formats = afficher_menu_format()

    # Extraction
    emails = fetch_emails(mail, dossier=dossier, critere=critere, limite=limite)
    mail.logout()

    if not emails:
        print("\n⚠️  Aucun email à exporter.")
        return

    # Dossier de sortie
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"emails_{timestamp}"

    if "csv" in formats:
        save_csv(emails, OUTPUT_DIR / f"{base_name}.csv")
    if "json" in formats:
        save_json(emails, OUTPUT_DIR / f"{base_name}.json")
    if "txt" in formats:
        save_txt(emails, OUTPUT_DIR / f"{base_name}.txt")

    print(f"\n🎉 Extraction terminée ! {len(emails)} email(s) exporté(s) dans → {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
