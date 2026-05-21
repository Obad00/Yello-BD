#!/usr/bin/env python3
"""Génère du contenu marketing (posts, emails) depuis une idée."""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


CONTENT_TYPES = {
    "linkedin": "Post LinkedIn professionnel (max 1300 caractères, avec accroche)",
    "instagram": "Légende Instagram engageante avec hashtags pertinents",
    "facebook": "Post Facebook informatif et accessible",
    "email": "Email court pour newsletter segment {segment}",
    "carousel": "Structure carrousel 5 slides (titre + texte par slide)",
    "video_script": "Script vidéo 60 secondes (accroche, corps, CTA)",
}


def generate(idee: str, content_type: str, segment: str = "Entreprise") -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    instruction = CONTENT_TYPES.get(content_type, CONTENT_TYPES["linkedin"]).format(segment=segment)

    if not api_key:
        return f"[Mode hors-ligne]\nIdée: {idee}\nType: {content_type}\n→ Configurez OPENAI_API_KEY pour génération IA."

    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "Tu rédiges du contenu pour Yello, EdTech IA. Ton expert mais accessible."},
            {"role": "user", "content": f"Idée: {idee}\n\nFormat demandé: {instruction}\nSegment cible: {segment}"},
        ],
        temperature=0.75,
        max_tokens=1200,
    )
    return (response.choices[0].message.content or "").strip()


def main():
    parser = argparse.ArgumentParser(description="Générateur de contenu Yello")
    parser.add_argument("idee", help="Idée ou thème du contenu")
    parser.add_argument(
        "-t", "--type",
        choices=list(CONTENT_TYPES.keys()),
        default="linkedin",
    )
    parser.add_argument("-s", "--segment", default="Entreprise")
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    content = generate(args.idee, args.type, args.segment)
    result = {"idee": args.idee, "type": args.type, "segment": args.segment, "content": content}

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"💾 Sauvegardé → {args.output}")
    else:
        print(content)


if __name__ == "__main__":
    main()
