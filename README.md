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
```

Email is optional, but when an email is given it must be a valid address, for example `alice@example.com`. Invalid email addresses are rejected when a contact is added or updated.

The contact data is stored in a JSON file. Set `CONTACT_BOOK_DATA_FILE` to choose a custom storage location, or pass `--file <path>` before the command, for example `contact --file work.json list`. The `export` command writes all contacts to a CSV file with `id`, `name`, `phone`, and `email` columns.

## Development

```bash
python -m pytest
```

## License

MIT
