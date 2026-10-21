import csv
import tempfile
import unittest
from pathlib import Path

from expense_tracker.cli import main
from expense_tracker.db import ExpenseStore


class ExpenseStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = ExpenseStore(":memory:")

    def tearDown(self) -> None:
        self.store.close()

    def test_add_and_list(self) -> None:
        self.store.add(12.5, "Food", "lunch", "2026-10-01")
        rows = self.store.list()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].category, "food")  # normalised to lowercase
        self.assertAlmostEqual(rows[0].amount, 12.5)

    def test_rejects_bad_input(self) -> None:
        with self.assertRaises(ValueError):
            self.store.add(0, "food")
        with self.assertRaises(ValueError):
            self.store.add(5, "   ")
        with self.assertRaises(ValueError):
            self.store.add(5, "food", spent_on="01-10-2026")

    def test_filters(self) -> None:
        self.store.add(10, "food", spent_on="2026-09-15")
        self.store.add(20, "food", spent_on="2026-10-02")
        self.store.add(30, "rent", spent_on="2026-10-03")
        self.assertEqual(len(self.store.list(month="2026-10")), 2)
        self.assertEqual(len(self.store.list(category="FOOD")), 2)
        self.assertEqual(len(self.store.list(category="food", month="2026-10")), 1)

    def test_summary_sorted_by_total(self) -> None:
        self.store.add(10, "food", spent_on="2026-10-01")
        self.store.add(15, "food", spent_on="2026-10-02")
        self.store.add(100, "rent", spent_on="2026-10-03")
        self.assertEqual(self.store.summary(), [("rent", 100.0), ("food", 25.0)])

    def test_delete(self) -> None:
        expense_id = self.store.add(5, "misc")
        self.assertTrue(self.store.delete(expense_id))
        self.assertFalse(self.store.delete(expense_id))

    def test_export_csv(self) -> None:
        self.store.add(7.25, "coffee", "flat white", "2026-10-05")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.csv"
            n = self.store.export_csv(out, self.store.list())
            self.assertEqual(n, 1)
            with open(out, newline="", encoding="utf-8") as fh:
                rows = list(csv.reader(fh))
        self.assertEqual(rows[0], ["id", "date", "category", "amount", "note"])
        self.assertEqual(rows[1][2:], ["coffee", "7.25", "flat white"])


class CliTests(unittest.TestCase):
    def test_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "test.db")
            self.assertEqual(main(["--db", db, "add", "9.99", "books", "-d", "2026-10-10"]), 0)
            self.assertEqual(main(["--db", db, "list"]), 0)
            self.assertEqual(main(["--db", db, "summary"]), 0)
            self.assertEqual(main(["--db", db, "delete", "999"]), 1)
            self.assertEqual(main(["--db", db, "add", "-5", "books"]), 2)


if __name__ == "__main__":
    unittest.main()
