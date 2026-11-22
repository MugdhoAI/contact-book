# Contact Book

A simple command line contact book with JSON file storage.

## Installation

```bash
python -m pip install -e ".[test]"
```

## Usage

```bash
contact add "Alice Smith" --phone "01700000000" --email "alice@example.com"
contact list
contact count
contact search Alice
contact show 1
contact update 1 --phone "01800000000"
contact delete 1
contact export contacts.csv
contact import contacts.csv
```

Email is optional, but when an email is given it must be a valid address, for example `alice@example.com`. Invalid email addresses are rejected when a contact is added or updated.

The contact data is stored in a JSON file. Set `CONTACT_BOOK_DATA_FILE` to choose a custom storage location, or pass `--file <path>` before the command, for example `contact --file work.json list`. The `export` command writes all contacts to a CSV file with `id`, `name`, `phone`, and `email` columns. The `import` command reads contacts back from a CSV file with those columns: each row goes through the same validation and duplicate email checks as `add`, rows that fail are rejected and reported, and imported contacts get fresh ids, so an exported file can be imported into an empty contact book to restore its contacts.

## Development

```bash
python -m pytest
```

## License

MIT
