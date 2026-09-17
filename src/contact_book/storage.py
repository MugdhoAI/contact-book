"""JSON file persistence for contacts."""

import json
import os
from pathlib import Path

from .models import Contact

DEFAULT_DATA_FILE = Path("contacts.json")


class ContactStorage:
    """Read and write contacts as JSON."""

    def __init__(self, path: Path | None = None) -> None:
        configured_path = os.getenv("CONTACT_BOOK_DATA_FILE")
        self.path = path or (Path(configured_path) if configured_path else DEFAULT_DATA_FILE)

    def load(self) -> list[Contact]:
        if not self.path.exists():
            return []

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Contact storage contains invalid JSON.") from exc

        if not isinstance(raw, list):
            raise ValueError("Contact storage must contain a JSON list.")

        return [Contact.from_dict(item) for item in raw]

    def save(self, contacts: list[Contact]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        payload = [contact.to_dict() for contact in contacts]
        temporary_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(self.path)
