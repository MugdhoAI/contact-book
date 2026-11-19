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
    return parser


def export_contacts_csv(contacts, path: Path) -> int:
    """Write contacts to a CSV file, returning how many were written."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "name", "phone", "email"])
        for contact in contacts:
            writer.writerow([contact.id, contact.name, contact.phone, contact.email])
    return len(contacts)


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
    except ValueError as exc:
        parser.error(str(exc))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
