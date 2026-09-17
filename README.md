# Contact Book

A simple command-line contact book with JSON file storage.

## Installation

```bash
python -m pip install -e ".[test]"
```

## Usage

```bash
contact add "Alice Smith" --phone "01700000000" --email "alice@example.com"
contact list
contact search Alice
contact show 1
contact update 1 --phone "01800000000"
contact delete 1
```

The contact data is stored in a JSON file. Set `CONTACT_BOOK_DATA_FILE` to choose a custom storage location.

## Development

```bash
python -m pytest
```

## License

MIT
