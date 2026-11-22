"""Command-line interface for Contact Book."""

import argparse
import csv
from pathlib import Path

from . import __version__
from .service import ContactService
from .storage import ContactStorage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="contact", description="Manage contacts stored in a JSON file.")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--file", default=None, help="Path to the contacts data file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="Add a contact")
    add.add_argument("name")
    add.add_argument("--phone", default="")
    add.add_argument("--email", default="")

    subparsers.add_parser("list", help="List all contacts")

    subparsers.add_parser("count", help="Show how many contacts are stored")

    search = subparsers.add_parser("search", help="Search contacts")
    search.add_argument("query")

    show = subparsers.add_parser("show", help="Show one contact")
    show.add_argument("id", type=int)

    update = subparsers.add_parser("update", help="Update a contact")
    update.add_argument("id", type=int)
    update.add_argument("--name")
    update.add_argument("--phone")
    update.add_argument("--email")

    delete = subparsers.add_parser("delete", help="Delete a contact")
    delete.add_argument("id", type=int)

    export = subparsers.add_parser("export", help="Export contacts to a CSV file")
    export.add_argument("path")

    import_csv = subparsers.add_parser("import", help="Import contacts from a CSV file")
    import_csv.add_argument("path")
    return parser


def export_contacts_csv(contacts, path: Path) -> int:
    """Write contacts to a CSV file, returning how many were written."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "name", "phone", "email"])
        for contact in contacts:
            writer.writerow([contact.id, contact.name, contact.phone, contact.email])
    return len(contacts)


def import_contacts_csv(service, path: Path) -> tuple[int, int]:
    """Import contacts from a CSV file, returning (imported, rejected) counts.

    Each row is added through ContactService.add_contact, so imported rows
    follow the same validation and duplicate email rules as the add command.
    A row that add_contact rejects is skipped and counted as rejected, and
    the remaining rows are still imported. The id column written by export
    is ignored: imported contacts get fresh ids from the add path.
    """
    imported = 0
    rejected = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                service.add_contact(
                    row.get("name") or "",
                    row.get("phone") or "",
                    row.get("email") or "",
                )
            except ValueError:
                rejected += 1
            else:
                imported += 1
    return imported, rejected


def format_contact(contact) -> str:
    return f"{contact.id}: {contact.name} | Phone: {contact.phone or '-'} | Email: {contact.email or '-'}"


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    storage = ContactStorage(Path(args.file)) if args.file else ContactStorage()
    service = ContactService(storage)

    try:
        if args.command == "add":
            contact = service.add_contact(args.name, args.phone, args.email)
            print(f"Added contact {contact.id}: {contact.name}")
        elif args.command == "list":
            contacts = service.list_contacts()
            if not contacts:
                print("No contacts found.")
            else:
                for contact in contacts:
                    print(format_contact(contact))
                noun = "contact" if len(contacts) == 1 else "contacts"
                print(f"{len(contacts)} {noun} stored.")
        elif args.command == "count":
            total = len(service.list_contacts())
            noun = "contact" if total == 1 else "contacts"
            print(f"{total} {noun} stored.")
        elif args.command == "search":
            contacts = service.search_contacts(args.query)
            if not contacts:
                print("No contacts found.")
            else:
                for contact in contacts:
                    print(format_contact(contact))
        elif args.command == "show":
            print(format_contact(service.get_contact(args.id)))
        elif args.command == "update":
            if args.name is None and args.phone is None and args.email is None:
                raise ValueError("Provide at least one field to update.")
            contact = service.update_contact(args.id, args.name, args.phone, args.email)
            print(f"Updated contact {contact.id}: {contact.name}")
        elif args.command == "delete":
            service.delete_contact(args.id)
            print(f"Deleted contact {args.id}.")
        elif args.command == "export":
            total = export_contacts_csv(service.list_contacts(), Path(args.path))
            noun = "contact" if total == 1 else "contacts"
            print(f"Exported {total} {noun} to {args.path}.")
        elif args.command == "import":
            imported, rejected = import_contacts_csv(service, Path(args.path))
            noun = "contact" if imported == 1 else "contacts"
            print(f"Imported {imported} {noun} from {args.path}.")
            if rejected:
                row_noun = "row" if rejected == 1 else "rows"
                print(f"Rejected {rejected} {row_noun}.")
    except ValueError as exc:
        parser.error(str(exc))
    except OSError as exc:
        parser.error(str(exc))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
