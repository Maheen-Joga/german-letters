from datetime import date
from pathlib import Path

from german_letters import Address

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
ME = Address("Alex Beispiel", "Musterstraße 12", "10115", "Berlin")
THEM = Address("Hausverwaltung Muster GmbH", "Beispielweg 3", "10117", "Berlin")


def d(text: str) -> date:
    return date.fromisoformat(text)
