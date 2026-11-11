"""Application logic for managing contacts."""

from .models import Contact
from .storage import ContactStorage


def _validate_email(email: str) -> None:
    """Reject email addresses that are clearly malformed.

    An empty email is allowed because the field is optional. A non-empty
    email must contain exactly one at sign, a non-empty local part, and a
    domain with at least one dot that is not at either end.
    """
    if not email:
        return
    if any(character.isspace() for character in email) or email.count("@") != 1:
        raise ValueError("Invalid email address.")
    local, domain = email.split("@")
    if not local or not domain:
        raise ValueError("Invalid email address.")
    if "." not in domain or domain.startswith(".") or domain.endswith(".") or ".." in domain:
        raise ValueError("Invalid email address.")


def _ensure_email_available(contacts: list[Contact], email: str, exclude_id: int | None = None) -> None:
    """Reject an email that another contact already uses, ignoring case."""
    if not email:
        return
    for contact in contacts:
        if contact.id != exclude_id and contact.email.lower() == email.lower():
            raise ValueError("A contact with this email already exists.")


class ContactService:
    """Manage contacts using a persistent storage backend."""

    def __init__(self, storage: ContactStorage) -> None:
        self.storage = storage

    def list_contacts(self) -> list[Contact]:
        return sorted(self.storage.load(), key=lambda contact: (contact.name.lower(), contact.id))

    def add_contact(self, name: str, phone: str = "", email: str = "") -> Contact:
        name = name.strip()
        phone = phone.strip()
        email = email.strip()
        if not name:
            raise ValueError("Name cannot be empty.")
        _validate_email(email)

        contacts = self.storage.load()
        _ensure_email_available(contacts, email)
        next_id = max((contact.id for contact in contacts), default=0) + 1
        contact = Contact(next_id, name, phone, email)
        self.storage.save([*contacts, contact])
        return contact

    def get_contact(self, contact_id: int) -> Contact:
        for contact in self.storage.load():
            if contact.id == contact_id:
                return contact
        raise ValueError(f"Contact {contact_id} not found.")

    def search_contacts(self, query: str) -> list[Contact]:
        query = query.strip().lower()
        if not query:
            return []
        return [
            contact
            for contact in self.list_contacts()
            if query in contact.name.lower()
            or query in contact.phone.lower()
            or query in contact.email.lower()
        ]

    def update_contact(
        self,
        contact_id: int,
        name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
    ) -> Contact:
        contacts = self.storage.load()
        for index, contact in enumerate(contacts):
            if contact.id != contact_id:
                continue
            updated = Contact(
                id=contact.id,
                name=contact.name if name is None else name.strip(),
                phone=contact.phone if phone is None else phone.strip(),
                email=contact.email if email is None else email.strip(),
            )
            if not updated.name:
                raise ValueError("Name cannot be empty.")
            _validate_email(updated.email)
            _ensure_email_available(contacts, updated.email, exclude_id=contact.id)
            contacts[index] = updated
            self.storage.save(contacts)
            return updated
        raise ValueError(f"Contact {contact_id} not found.")

    def delete_contact(self, contact_id: int) -> None:
        contacts = self.storage.load()
        remaining = [contact for contact in contacts if contact.id != contact_id]
        if len(remaining) == len(contacts):
            raise ValueError(f"Contact {contact_id} not found.")
        self.storage.save(remaining)
