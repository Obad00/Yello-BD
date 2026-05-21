#!/usr/bin/env python3
"""Recalcule les scores sur un fichier JSON de contacts."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from yello.scoring.lead_scorer import score_contact_dict, classify_score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Fichier JSON contacts")
    parser.add_argument("-o", "--output", type=Path, help="Fichier de sortie")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        contacts = json.load(f)

    for c in contacts:
        score_contact_dict(c)

    out = args.output or args.input.with_stem(args.input.stem + "_scored")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)

    hot = sum(1 for c in contacts if c.get("score", 0) >= 61)
    print(f"✅ {len(contacts)} contacts scorés → {out}")
    print(f"🔥 Leads chauds (61+) : {hot}")


if __name__ == "__main__":
    main()
