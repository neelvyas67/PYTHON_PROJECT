"""Data access layer for the expense tracker (SQLite, standard library only)."""

from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

DEFAULT_DB = Path.home() / ".expense_tracker.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    spent_on    TEXT    NOT NULL,
    category    TEXT    NOT NULL,
    amount      REAL    NOT NULL CHECK (amount > 0),
    note        TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(spent_on);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);
"""


@dataclass(frozen=True)
class Expense:
    id: int
    spent_on: str
    category: str
    amount: float
    note: str


class ExpenseStore:
    """Thin wrapper around a SQLite database of expenses."""

    def __init__(self, path: str | Path = DEFAULT_DB) -> None:
        self._conn = sqlite3.connect(str(path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "ExpenseStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ---- commands -------------------------------------------------------

    def add(
        self,
        amount: float,
        category: str,
        note: str = "",
        spent_on: Optional[str] = None,
    ) -> int:
        if amount <= 0:
            raise ValueError("amount must be greater than zero")
        category = category.strip().lower()
        if not category:
            raise ValueError("category must not be empty")
        spent_on = spent_on or date.today().isoformat()
        date.fromisoformat(spent_on)  # validates the format, raises ValueError
        with self._conn:
            cur = self._conn.execute(
                "INSERT INTO expenses (spent_on, category, amount, note) VALUES (?, ?, ?, ?)",
                (spent_on, category, amount, note.strip()),
            )
        return int(cur.lastrowid)

    def delete(self, expense_id: int) -> bool:
        with self._conn:
            cur = self._conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return cur.rowcount > 0

    def list(
        self,
        category: Optional[str] = None,
        month: Optional[str] = None,
    ) -> list[Expense]:
        """List expenses, optionally filtered by category and/or month (YYYY-MM)."""
        query = "SELECT * FROM expenses WHERE 1=1"
        params: list[str] = []
        if category:
            query += " AND category = ?"
            params.append(category.strip().lower())
        if month:
            query += " AND substr(spent_on, 1, 7) = ?"
            params.append(month)
        query += " ORDER BY spent_on DESC, id DESC"
        return [Expense(**dict(r)) for r in self._conn.execute(query, params)]

    def summary(self, month: Optional[str] = None) -> list[tuple[str, float]]:
        """Total spend per category, largest first."""
        query = "SELECT category, SUM(amount) AS total FROM expenses"
        params: list[str] = []
        if month:
            query += " WHERE substr(spent_on, 1, 7) = ?"
            params.append(month)
        query += " GROUP BY category ORDER BY total DESC"
        return [(r["category"], float(r["total"])) for r in self._conn.execute(query, params)]

    def export_csv(self, path: str | Path, expenses: Iterable[Expense]) -> int:
        count = 0
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["id", "date", "category", "amount", "note"])
            for e in expenses:
                writer.writerow([e.id, e.spent_on, e.category, f"{e.amount:.2f}", e.note])
                count += 1
        return count
