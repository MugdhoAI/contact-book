from pathlib import Path

import pytest

from contact_book.models import Contact
from contact_book.service import ContactService
from contact_book.storage import ContactStorage


def make_service(tmp_path: Path) -> ContactService:
    return ContactService(ContactStorage(tmp_path / "contacts.json"))


def test_add_and_load_contact(tmp_path):
    service = make_service(tmp_path)
    created = service.add_contact("Alice Smith", "01700000000", "alice@example.com")

    assert created == Contact(1, "Alice Smith", "01700000000", "alice@example.com")
    assert service.get_contact(1) == created


def test_contacts_persist_between_service_instances(tmp_path):
    service = make_service(tmp_path)
    service.add_contact("Bob", "01800000000")

    reloaded = make_service(tmp_path)
    assert reloaded.list_contacts()[0].name == "Bob"


def test_search_matches_name_phone_and_email(tmp_path):
    service = make_service(tmp_path)
    service.add_contact("Alice Smith", "01712345678", "alice@example.com")
    service.add_contact("Bob Jones", "01899999999", "bob@example.com")

    assert len(service.search_contacts("alice")) == 1
    assert len(service.search_contacts("0189")) == 1
    assert len(service.search_contacts("@example.com")) == 2


def test_update_contact(tmp_path):
    service = make_service(tmp_path)
    service.add_contact("Alice", "01700000000", "alice@example.com")

    updated = service.update_contact(1, phone="01800000000")

    assert updated == Contact(1, "Alice", "01800000000", "alice@example.com")


def test_delete_contact(tmp_path):
    service = make_service(tmp_path)
    service.add_contact("Alice")

    service.delete_contact(1)

    assert service.list_contacts() == []
    with pytest.raises(ValueError, match="not found"):
        service.get_contact(1)


def test_empty_name_is_rejected(tmp_path):
    service = make_service(tmp_path)

    with pytest.raises(ValueError, match="Name cannot be empty"):
        service.add_contact("   ")


def test_missing_contact_is_rejected(tmp_path):
    service = make_service(tmp_path)

    with pytest.raises(ValueError, match="Contact 99 not found"):
        service.get_contact(99)
