#!/usr/bin/env python3
"""Pointe vers la création automatique du CRM Airtable."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    print("Redirection vers create_airtable_crm.py …\n")
    script = ROOT / "scripts" / "create_airtable_crm.py"
    args = [sys.executable, str(script)] + sys.argv[1:]
    sys.exit(subprocess.call(args))


if __name__ == "__main__":
    main()
