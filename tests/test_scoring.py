"""Tests unitaires — scoring leads."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from yello.scoring.lead_scorer import (
    compute_score,
    classify_score,
    is_professional_email,
    is_decision_maker_role,
)


def test_professional_email():
    assert is_professional_email("contact@ecole.fr") is True
    assert is_professional_email("user@gmail.com") is False


def test_decision_maker():
    assert is_decision_maker_role("Directeur pédagogique") is True
    assert is_decision_maker_role("Stagiaire marketing") is False


def test_score_cold():
    s = compute_score(email="user@gmail.com")
    assert s <= 30
    assert classify_score(s) == "Lead froid"


def test_score_hot():
    s = compute_score(
        email="dir@universite.fr",
        telephone="+33 6 12 34 56 78",
        poste="Directeur formation",
        organisation="Université Paris",
        meeting_booked=True,
    )
    assert s >= 61
    assert classify_score(s) in ("Lead chaud", "Priorité commerciale")


if __name__ == "__main__":
    test_professional_email()
    test_decision_maker()
    test_score_cold()
    test_score_hot()
    print("✅ Tous les tests passent")
