"""Focused checks for data boundaries and user-facing failures."""

import csv
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from app.core import ask, build, money, parse_date
from evals.test_app import row


class CleaningTests(unittest.TestCase):
    def test_date_conventions_and_invalid_input(self):
        self.assertEqual(parse_date("05-01-2024"), ("2024-01-05", True))
        self.assertEqual(parse_date("01/05/2024"), ("2024-01-05", True))
        self.assertEqual(parse_date("2024-02-30")[0], None)

    def test_currency_mismatch_and_invalid_amount_are_excluded(self):
        self.assertIsNone(money("100 EUR", "USD"))
        self.assertIsNone(money("NaN", "USD"))
        self.assertEqual(money("£12.50", "GBP"), 1588)

    def test_latest_snapshot_wins_over_earlier_invoice(self):
        db, _ = build(
            [row("1", "A", seats="2"), row("2", "A", seats="3", invoice_date="2024-02-01")]
        )
        result = ask(db, "Which region has the highest average MRR per account?")
        self.assertEqual(result["rows"], [("NA", 26730.0, 1)])

    def test_conflicting_duplicate_keeps_first_and_exact_duplicate_count(self):
        original = row("1", "A")
        db, quality = build([original, original.copy(), row("1", "A", amount="999")])
        self.assertEqual((quality["exact_duplicate_rows"], quality["conflicting_ids"]), (1, 1))
        self.assertEqual(db.execute("SELECT usd_cents FROM invoices").fetchone(), (10800,))

    def test_database_is_query_only_after_build(self):
        db, _ = build([row("1", "A")])
        with self.assertRaises(sqlite3.OperationalError):
            db.execute("DELETE FROM invoices")

    def test_invalid_or_missing_rows_do_not_become_revenue(self):
        db, quality = build(
            [
                row("1", "A", amount="100 EUR", currency="USD"),
                row("2", "B", status="refund", amount="10"),
            ]
        )
        result = ask(db, "What was our total recognized revenue in USD for paid invoices in 2024?")
        self.assertEqual(result["rows"][0], (2024, 0, 0, 0))
        self.assertEqual((quality["invalid_usd_amount"], quality["positive_refunds"]), (1, 1))


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "app", *args], capture_output=True, text=True, check=False
        )

    def test_unsupported_question_returns_error(self):
        result = self.run_cli("--question", "Delete all invoices")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unsupported question", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_short_csv_row_is_reported_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.csv"
            fields = list(row("1", "A"))
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(fields)
                writer.writerow(["INV-1"])
            result = self.run_cli("--csv", str(path))
        self.assertEqual(result.returncode, 2)
        self.assertIn("CSV", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_extra_csv_field_is_reported_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "extra.csv"
            record = row("1", "A")
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(record.keys())
                writer.writerow([*record.values(), "unexpected"])
            result = self.run_cli("--csv", str(path))
        self.assertEqual(result.returncode, 2)
        self.assertIn("CSV", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
