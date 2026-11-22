from pathlib import Path

import pytest

from contact_book.cli import export_contacts_csv, import_contacts_csv, main
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


def test_search_matches_phone_by_digits_ignoring_separators(tmp_path):
    service = make_service(tmp_path)
    service.add_contact("Alice Smith", "+880 1700-000000", "alice@example.com")
    service.add_contact("Bob Jones", "01899999999", "bob@example.com")

    assert [contact.name for contact in service.search_contacts("01700000000")] == ["Alice Smith"]
    assert [contact.name for contact in service.search_contacts("+8801700000000")] == ["Alice Smith"]
    assert len(service.search_contacts("0189")) == 1


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


def test_add_collapses_repeated_whitespace_in_name(tmp_path):
    service = make_service(tmp_path)

    created = service.add_contact("Alice   Smith", "01700000000")
    assert created.name == "Alice Smith"

    updated = service.update_contact(1, name="  Alice   Jane   Smith  ")
    assert updated.name == "Alice Jane Smith"


def test_empty_name_is_rejected(tmp_path):
    service = make_service(tmp_path)

    with pytest.raises(ValueError, match="Name cannot be empty"):
        service.add_contact("   ")


def test_add_rejects_invalid_email(tmp_path):
    service = make_service(tmp_path)

    for invalid in ("not-an-email", "alice@", "@example.com", "alice@example", "alice @example.com", "alice@example..com"):
        with pytest.raises(ValueError, match="Invalid email address"):
            service.add_contact("Alice", email=invalid)

    assert service.list_contacts() == []


def test_add_allows_empty_and_valid_email(tmp_path):
    service = make_service(tmp_path)

    without_email = service.add_contact("Alice")
    with_email = service.add_contact("Bob", email="bob@example.com")

    assert without_email.email == ""
    assert with_email.email == "bob@example.com"


def test_update_rejects_invalid_email_and_keeps_original(tmp_path):
    service = make_service(tmp_path)
    service.add_contact("Alice", "01700000000", "alice@example.com")

    with pytest.raises(ValueError, match="Invalid email address"):
        service.update_contact(1, email="alice@invalid")

    assert service.get_contact(1).email == "alice@example.com"


def test_missing_contact_is_rejected(tmp_path):
    service = make_service(tmp_path)

    with pytest.raises(ValueError, match="Contact 99 not found"):
        service.get_contact(99)


def test_add_rejects_duplicate_email_ignoring_case(tmp_path):
    service = make_service(tmp_path)
    service.add_contact("Alice", email="alice@example.com")

    with pytest.raises(ValueError, match="already exists"):
        service.add_contact("Alicia", email="ALICE@example.com")

    assert len(service.list_contacts()) == 1


def test_update_rejects_duplicate_email_and_keeps_original(tmp_path):
    service = make_service(tmp_path)
    service.add_contact("Alice", email="alice@example.com")
    service.add_contact("Bob", email="bob@example.com")

    with pytest.raises(ValueError, match="already exists"):
        service.update_contact(2, email="Alice@Example.com")

    assert service.get_contact(2).email == "bob@example.com"


def test_update_allows_keeping_own_email(tmp_path):
    service = make_service(tmp_path)
    service.add_contact("Alice", "01700000000", "alice@example.com")

    updated = service.update_contact(1, email="alice@example.com", phone="01800000000")

    assert updated.phone == "01800000000"


def test_add_rejects_invalid_phone(tmp_path):
    service = make_service(tmp_path)

    for invalid in ("call-me", "123", "+880 123", "01700000000000000000"):
        with pytest.raises(ValueError, match="Invalid phone number"):
            service.add_contact("Alice", phone=invalid)

    assert service.list_contacts() == []


def test_add_allows_common_phone_formats(tmp_path):
    service = make_service(tmp_path)

    assert service.add_contact("Alice", phone="+880 1700-000000").phone == "+880 1700-000000"
    assert service.add_contact("Bob", phone="(017) 000 0000").phone == "(017) 000 0000"
    assert service.add_contact("Cid").phone == ""


def test_update_rejects_invalid_phone_and_keeps_original(tmp_path):
    service = make_service(tmp_path)
    service.add_contact("Alice", "01700000000", "alice@example.com")

    with pytest.raises(ValueError, match="Invalid phone number"):
        service.update_contact(1, phone="not a number")

    assert service.get_contact(1).phone == "01700000000"


def test_load_reports_malformed_entries_with_a_clear_error(tmp_path):
    path = tmp_path / "contacts.json"
    service = ContactService(ContactStorage(path))

    path.write_text('[{"name": "No ID"}]', encoding="utf-8")
    with pytest.raises(ValueError, match="invalid entry"):
        service.list_contacts()

    path.write_text('["just a string"]', encoding="utf-8")
    with pytest.raises(ValueError, match="invalid entry"):
        service.list_contacts()


def test_cli_count_reports_number_of_contacts(tmp_path, monkeypatch, capsys):
    data_file = tmp_path / "cli-contacts.json"
    service = ContactService(ContactStorage(data_file))

    monkeypatch.setattr("sys.argv", ["contact", "--file", str(data_file), "count"])
    assert main() == 0
    assert "0 contacts stored." in capsys.readouterr().out

    service.add_contact("Alice")
    service.add_contact("Bob")

    monkeypatch.setattr("sys.argv", ["contact", "--file", str(data_file), "count"])
    assert main() == 0
    assert "2 contacts stored." in capsys.readouterr().out

    service.delete_contact(2)
    monkeypatch.setattr("sys.argv", ["contact", "--file", str(data_file), "count"])
    assert main() == 0
    assert "1 contact stored." in capsys.readouterr().out


def test_cli_export_writes_contacts_to_csv(tmp_path, monkeypatch, capsys):
    data_file = tmp_path / "cli-contacts.json"
    export_file = tmp_path / "contacts.csv"
    service = ContactService(ContactStorage(data_file))
    service.add_contact("Alice Smith", "01700000000", "alice@example.com")
    service.add_contact("Bob Jones")

    monkeypatch.setattr("sys.argv", ["contact", "--file", str(data_file), "export", str(export_file)])
    assert main() == 0
    assert "Exported 2 contacts to" in capsys.readouterr().out

    rows = export_file.read_text(encoding="utf-8").splitlines()
    assert rows[0] == "id,name,phone,email"
    assert rows[1] == "1,Alice Smith,01700000000,alice@example.com"
    assert rows[2] == "2,Bob Jones,,"


def test_csv_import_round_trip_restores_contacts(tmp_path, monkeypatch, capsys):
    source = make_service(tmp_path / "source")
    source.add_contact("Alice Smith", "01700000000", "alice@example.com")
    source.add_contact("Bob Jones", "01899999999", "bob@example.com")
    source.add_contact("Cid Ray")
    export_file = tmp_path / "contacts.csv"
    assert export_contacts_csv(source.list_contacts(), export_file) == 3

    data_file = tmp_path / "restored.json"
    monkeypatch.setattr("sys.argv", ["contact", "--file", str(data_file), "import", str(export_file)])
    assert main() == 0
    assert "Imported 3 contacts from" in capsys.readouterr().out

    restored = ContactService(ContactStorage(data_file))
    assert [(contact.name, contact.phone, contact.email) for contact in restored.list_contacts()] == [
        (contact.name, contact.phone, contact.email) for contact in source.list_contacts()
    ]
    assert [contact.id for contact in restored.list_contacts()] == [1, 2, 3]


def test_csv_import_rejects_invalid_rows_and_imports_valid_ones(tmp_path):
    import_file = tmp_path / "import.csv"
    import_file.write_text(
        "id,name,phone,email\n"
        "1,Alice Smith,01700000000,alice@example.com\n"
        "2,Bad Email,01700000000,not-an-email\n"
        "3,,01700000000,no-name@example.com\n"
        "4,Bad Phone,call-me,bad-phone@example.com\n"
        "5,Bob Jones,01899999999,bob@example.com\n",
        encoding="utf-8",
    )
    service = make_service(tmp_path)

    imported, rejected = import_contacts_csv(service, import_file)

    assert (imported, rejected) == (2, 3)
    assert [contact.name for contact in service.list_contacts()] == ["Alice Smith", "Bob Jones"]


def test_csv_import_rejects_duplicate_emails(tmp_path, monkeypatch, capsys):
    data_file = tmp_path / "cli-contacts.json"
    service = ContactService(ContactStorage(data_file))
    service.add_contact("Alice Smith", "01700000000", "alice@example.com")
    import_file = tmp_path / "import.csv"
    import_file.write_text(
        "id,name,phone,email\n"
        "1,Alicia,01800000000,ALICE@example.com\n"
        "2,Bob Jones,01899999999,bob@example.com\n"
        "3,Bobby,01900000000,Bob@Example.com\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["contact", "--file", str(data_file), "import", str(import_file)])
    assert main() == 0
    output = capsys.readouterr().out
    assert "Imported 1 contact from" in output
    assert "Rejected 2 rows." in output

    assert [contact.name for contact in service.list_contacts()] == ["Alice Smith", "Bob Jones"]
    assert service.get_contact(1).email == "alice@example.com"


def test_export_contacts_csv_returns_count(tmp_path):
    contacts = [Contact(1, "Alice", "01700000000", "alice@example.com")]
    export_file = tmp_path / "out.csv"

    assert export_contacts_csv(contacts, export_file) == 1
    assert "alice@example.com" in export_file.read_text(encoding="utf-8")


def test_cli_update_search_show_and_delete(tmp_path, monkeypatch, capsys):
    data_file = tmp_path / "cli-contacts.json"
    service = ContactService(ContactStorage(data_file))
    service.add_contact("Alice Smith", "01700000000", "alice@example.com")
    service.add_contact("Bob Jones", "01899999999", "bob@example.com")

    monkeypatch.setattr("sys.argv", ["contact", "--file", str(data_file), "update", "1", "--phone", "01800000000"])
    assert main() == 0
    assert "Updated contact 1: Alice Smith" in capsys.readouterr().out

    monkeypatch.setattr("sys.argv", ["contact", "--file", str(data_file), "search", "0180"])
    assert main() == 0
    assert "Alice Smith" in capsys.readouterr().out

    monkeypatch.setattr("sys.argv", ["contact", "--file", str(data_file), "show", "2"])
    assert main() == 0
    assert "2: Bob Jones" in capsys.readouterr().out

    monkeypatch.setattr("sys.argv", ["contact", "--file", str(data_file), "delete", "2"])
    assert main() == 0
    assert "Deleted contact 2." in capsys.readouterr().out
    assert service.list_contacts()[0].name == "Alice Smith"


def test_cli_update_without_fields_is_rejected(tmp_path, monkeypatch):
    data_file = tmp_path / "cli-contacts.json"
    service = ContactService(ContactStorage(data_file))
    service.add_contact("Alice")

    monkeypatch.setattr("sys.argv", ["contact", "--file", str(data_file), "update", "1"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 2
    assert service.get_contact(1).name == "Alice"


def test_cli_show_missing_contact_is_rejected(tmp_path, monkeypatch):
    data_file = tmp_path / "cli-contacts.json"

    monkeypatch.setattr("sys.argv", ["contact", "--file", str(data_file), "show", "99"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 2


def test_cli_add_and_list_with_file_option(tmp_path, monkeypatch, capsys):
    data_file = tmp_path / "cli-contacts.json"

    monkeypatch.setattr("sys.argv", ["contact", "--file", str(data_file), "add", "Alice", "--email", "alice@example.com"])
    assert main() == 0
    assert "Added contact 1: Alice" in capsys.readouterr().out

    monkeypatch.setattr("sys.argv", ["contact", "--file", str(data_file), "list"])
    assert main() == 0
    output = capsys.readouterr().out
    assert "Alice" in output
    assert "1 contact stored." in output


def test_email_is_stored_in_lowercase(tmp_path):
    service = make_service(tmp_path)

    created = service.add_contact("Alice", email="Alice@Example.COM")
    assert created.email == "alice@example.com"

    updated = service.update_contact(1, email="ALICE@Example.com")
    assert updated.email == "alice@example.com"

    assert len(service.search_contacts("ALICE@EXAMPLE.COM")) == 1
