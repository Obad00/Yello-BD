"""Modèle de contact CRM Yello."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class Contact:
    nom: str = ""
    prenom: str = ""
    email: str = ""
    telephone: str = ""
    whatsapp: str = ""
    linkedin: str = ""
    organisation: str = ""
    poste: str = ""
    pays: str = ""
    ville: str = ""
    source: str = "Gmail"
    segment: str = "Non classé"
    statut_commercial: str = "Nouveau lead"
    score: int = 0
    dernier_contact: str = ""
    prochaine_action: str = ""
    commentaires: str = ""
    sujet_discussion: str = ""
    tags_contexte: list[str] = field(default_factory=list)
    consentement_newsletter: bool = False
    email_message_id: str = ""

    def to_airtable_fields(self) -> dict[str, Any]:
        """Convertit le contact en champs Airtable."""
        fields: dict[str, Any] = {
            "Nom": self.nom or self.prenom or "Inconnu",
            "Prénom": self.prenom,
            "Email": self.email,
            "Téléphone": self.telephone,
            "WhatsApp": self.whatsapp,
            "LinkedIn": self.linkedin,
            "Organisation": self.organisation,
            "Poste": self.poste,
            "Pays": self.pays,
            "Ville": self.ville,
            "Source": self.source,
            "Segment": self.segment,
            "Statut commercial": self.statut_commercial,
            "Score du lead": self.score,
            "Prochaine action": self.prochaine_action,
            "Commentaires": self.commentaires,
            "Sujet discussion": self.sujet_discussion,
            "Consentement newsletter": self.consentement_newsletter,
        }
        if self.dernier_contact:
            fields["Dernier contact"] = self.dernier_contact
        if self.tags_contexte:
            fields["Tags contexte"] = self.tags_contexte
        return {k: v for k, v in fields.items() if v not in ("", None, [], False) or k == "Consentement newsletter"}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_parsed_email(cls, parsed: dict[str, Any]) -> Contact:
        return cls(
            nom=parsed.get("nom", ""),
            prenom=parsed.get("prenom", ""),
            email=parsed.get("email", ""),
            telephone=parsed.get("telephone", ""),
            organisation=parsed.get("organisation", ""),
            poste=parsed.get("poste", ""),
            source="Gmail",
            segment=parsed.get("segment", "Non classé"),
            sujet_discussion=parsed.get("sujet", ""),
            commentaires=parsed.get("signature", ""),
            tags_contexte=parsed.get("tags", []),
            email_message_id=parsed.get("message_id", ""),
            dernier_contact=datetime.now().strftime("%Y-%m-%d"),
        )
