"""Command-line interface for the expense tracker."""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from . import __version__
from .db import DEFAULT_DB, ExpenseStore


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="expense-tracker", description="Track your spending from the terminal.")
    p.add_argument("--db", default=str(DEFAULT_DB), help="path to the SQLite database file")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="record a new expense")
    add.add_argument("amount", type=float)
    add.add_argument("category")
    add.add_argument("-n", "--note", default="")
    add.add_argument("-d", "--date", help="YYYY-MM-DD (defaults to today)")

    ls = sub.add_parser("list", help="list expenses")
    ls.add_argument("-c", "--category")
    ls.add_argument("-m", "--month", help="YYYY-MM")

    rm = sub.add_parser("delete", help="delete an expense by id")
    rm.add_argument("id", type=int)

    sm = sub.add_parser("summary", help="total spend per category")
    sm.add_argument("-m", "--month", help="YYYY-MM")

    ex = sub.add_parser("export", help="export expenses to CSV")
    ex.add_argument("path")
    ex.add_argument("-c", "--category")
    ex.add_argument("-m", "--month", help="YYYY-MM")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with ExpenseStore(args.db) as store:
            return _dispatch(store, args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _dispatch(store: ExpenseStore, args: argparse.Namespace) -> int:
    if args.command == "add":
        new_id = store.add(args.amount, args.category, args.note, args.date)
        print(f"Added expense #{new_id}")
    elif args.command == "list":
        rows = store.list(args.category, args.month)
        if not rows:
            print("No expenses found.")
        for e in rows:
            print(f"#{e.id:<4} {e.spent_on}  {e.category:<14} {e.amount:>10.2f}  {e.note}")
    elif args.command == "delete":
        if store.delete(args.id):
            print(f"Deleted expense #{args.id}")
        else:
            print(f"No expense with id {args.id}", file=sys.stderr)
            return 1
    elif args.command == "summary":
        rows = store.summary(args.month)
        if not rows:
            print("No expenses found.")
        total = sum(t for _, t in rows)
        for category, amount in rows:
            share = amount / total * 100
            print(f"{category:<14} {amount:>10.2f}  {share:5.1f}%")
        if rows:
            print(f"{'TOTAL':<14} {total:>10.2f}")
    elif args.command == "export":
        n = store.export_csv(args.path, store.list(args.category, args.month))
        print(f"Exported {n} expense(s) to {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
