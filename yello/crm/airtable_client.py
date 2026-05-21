"""Client CRM Airtable pour Yello."""

from __future__ import annotations

import os
from typing import Any

from yello.models.contact import Contact


class AirtableCRM:
    def __init__(
        self,
        api_key: str | None = None,
        base_id: str | None = None,
        table_name: str | None = None,
    ):
        self.api_key = api_key or os.getenv("AIRTABLE_API_KEY", "")
        self.base_id = base_id or os.getenv("AIRTABLE_BASE_ID", "")
        self.table_name = table_name or os.getenv("AIRTABLE_TABLE_CONTACTS", "Contacts")
        self._table = None

    def _get_table(self):
        if self._table is not None:
            return self._table
        try:
            from pyairtable import Api
        except ImportError as e:
            raise ImportError(
                "Installez pyairtable : pip install pyairtable"
            ) from e
        if not self.api_key or not self.base_id:
            raise ValueError("AIRTABLE_API_KEY et AIRTABLE_BASE_ID requis dans .env")
        api = Api(self.api_key)
        self._table = api.table(self.base_id, self.table_name)
        return self._table

    def find_by_email(self, email: str) -> dict[str, Any] | None:
        table = self._get_table()
        formula = f"LOWER({{Email}}) = '{email.lower().replace(chr(39), chr(39)+chr(39))}'"
        records = table.all(formula=formula, max_records=1)
        return records[0] if records else None

    def upsert_contact(self, contact: Contact) -> dict[str, Any]:
        """Crée ou met à jour un contact (détection doublon par email)."""
        table = self._get_table()
        fields = contact.to_airtable_fields()
        existing = self.find_by_email(contact.email)

        if existing:
            record_id = existing["id"]
            updated = table.update(record_id, fields)
            return {"action": "updated", "record": updated}

        created = table.create(fields)
        return {"action": "created", "record": created}

    def upsert_from_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        contact = Contact(
            nom=data.get("nom", ""),
            prenom=data.get("prenom", ""),
            email=data.get("email", ""),
            telephone=data.get("telephone", ""),
            linkedin=data.get("linkedin", ""),
            organisation=data.get("organisation", ""),
            poste=data.get("poste", ""),
            source=data.get("source", "Gmail"),
            segment=data.get("segment", "Non classé"),
            score=data.get("score", 0),
            sujet_discussion=data.get("sujet", ""),
            commentaires=data.get("signature", "")[:1000],
            tags_contexte=data.get("tags", []),
            dernier_contact=data.get("dernier_contact", ""),
        )
        return self.upsert_contact(contact)

    def list_all(self, max_records: int = 100) -> list[dict[str, Any]]:
        return self._get_table().all(max_records=max_records)
