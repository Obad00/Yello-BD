"""Classification IA optionnelle (OpenAI) pour segments et intentions."""

from __future__ import annotations

import json
import os
from typing import Any


SEGMENTS = [
    "Apprenant", "Parent", "Professeur", "Formateur", "École", "Université",
    "Entreprise", "Incubateur", "ONG", "Institution publique", "Investisseur",
    "Partenaire stratégique", "Média", "Non classé",
]


def classify_with_openai(contact: dict[str, Any]) -> dict[str, Any]:
    """
    Enrichit le contact avec segment et intention via OpenAI.
    Nécessite OPENAI_API_KEY dans l'environnement.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return contact

    try:
        from openai import OpenAI
    except ImportError:
        return contact

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    prompt = f"""Analyse ce contact professionnel pour Yello (EdTech / IA éducation).
Retourne UNIQUEMENT un JSON valide avec les clés:
- segment (une valeur parmi: {', '.join(SEGMENTS)})
- intention (question_produit | demande_demo | partenariat | presse | autre)
- resume_besoin (une phrase)

Contact:
Email: {contact.get('email')}
Organisation: {contact.get('organisation')}
Poste: {contact.get('poste')}
Sujet email: {contact.get('sujet')}
Extrait signature: {contact.get('signature', '')[:400]}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Tu es un assistant CRM. Réponds uniquement en JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"
    try:
        result = json.loads(content)
        if result.get("segment") in SEGMENTS:
            contact["segment"] = result["segment"]
        contact["intention"] = result.get("intention", "autre")
        contact["resume_besoin"] = result.get("resume_besoin", "")
    except json.JSONDecodeError:
        pass

    return contact


def generate_linkedin_message(contact: dict[str, Any], step: str = "connexion") -> str:
    """Génère un message LinkedIn personnalisé pour une étape de séquence."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_message(contact, step)

    try:
        from openai import OpenAI
    except ImportError:
        return _fallback_message(contact, step)

    steps = {
        "connexion": "message de demande de connexion LinkedIn (court, personnalisé)",
        "presentation": "message de présentation Yello après connexion acceptée",
        "cas_usage": "message partageant un cas d'usage Yello en éducation/IA",
        "rdv": "message proposant un rendez-vous Calendly",
        "relance": "relance douce et professionnelle",
    }

    client = OpenAI(api_key=api_key)
    prompt = f"""Rédige un {steps.get(step, steps['presentation'])} pour:
- {contact.get('prenom')} {contact.get('nom')}
- {contact.get('poste')} chez {contact.get('organisation')}
- Segment: {contact.get('segment')}
Ton: professionnel, chaleureux, max 300 caractères pour connexion, 500 sinon.
Produit: Yello — plateforme éducative IA.
"""

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=400,
    )
    return (response.choices[0].message.content or "").strip()


def _fallback_message(contact: dict[str, Any], step: str) -> str:
    name = contact.get("prenom") or contact.get("nom") or "Bonjour"
    org = contact.get("organisation", "votre organisation")
    templates = {
        "connexion": f"Bonjour {name}, je souhaite échanger sur l'innovation éducative chez {org}.",
        "presentation": f"Bonjour {name}, Yello aide les équipes pédagogiques à intégrer l'IA. Intéressé(e) par un échange ?",
        "cas_usage": f"Bonjour {name}, une école partenaire a amélioré l'engagement apprenant avec Yello. Je peux vous partager le cas.",
        "rdv": f"Bonjour {name}, seriez-vous disponible pour 20 min cette semaine ? Lien Calendly sur demande.",
        "relance": f"Bonjour {name}, je me permets une relance — toujours partant(e) pour découvrir Yello ?",
    }
    return templates.get(step, templates["presentation"])
