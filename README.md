# Expense Tracker (Python)

A lightweight command-line expense tracker backed by SQLite. No third-party dependencies.

## Features
- Add, list, delete expenses
- Filter by category and month
- Per-category summary with percentage share
- Export to CSV
- Input validation and unit tests

## Requirements
Python 3.9+

## Install & run
```bash
pip install -e .
expense-tracker add 12.50 food -n "lunch"
expense-tracker add 800 rent -d 2026-10-01
expense-tracker list -m 2026-10
expense-tracker summary
expense-tracker export october.csv -m 2026-10
```
Or without installing: `python -m expense_tracker summary`.

Use `--db path/to/file.db` to choose the database file (default: `~/.expense_tracker.db`).

## Tests
```bash
python -m unittest discover -s tests -v
```

## Project structure
```
expense_tracker/
  db.py     # SQLite data layer
  cli.py    # argparse CLI
tests/      # unittest suite
```

## License
MIT
