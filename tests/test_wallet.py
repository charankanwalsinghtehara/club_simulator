import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from wallet import Wallet


class WalletTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.save_path = Path(self.temp_dir.name) / "wallet.json"
        self.wallet = Wallet(self.save_path)

    def test_starting_balance_and_atomic_persisted_purchase(self):
        self.assertEqual(self.wallet.balance, 10_000)
        result = self.wallet.purchase(
            "normal_entry",
            "Normal entry",
            500,
            idempotency_key="normal-1",
            grants=("normal_entry",),
        )
        self.assertEqual((result.status, result.balance), ("purchased", 9_500))

        loaded = Wallet(self.save_path)
        self.assertEqual(loaded.balance, 9_500)
        self.assertTrue(loaded.has_access("normal_entry"))
        self.assertEqual(loaded.transactions[0]["id"], "normal-1")

    def test_duplicate_and_already_owned_access_are_not_charged(self):
        arguments = {
            "item_id": "normal_entry",
            "title": "Normal entry",
            "price": 500,
            "grants": ("normal_entry",),
        }
        first = self.wallet.purchase(**arguments, idempotency_key="purchase-1")
        duplicate = self.wallet.purchase(**arguments, idempotency_key="purchase-1")
        second_request = self.wallet.purchase(**arguments, idempotency_key="purchase-2")

        self.assertEqual(first.balance, 9_500)
        self.assertEqual(duplicate.status, "duplicate")
        self.assertEqual(second_request.status, "already_unlocked")
        self.assertEqual(self.wallet.balance, 9_500)
        self.assertEqual(len(self.wallet.transactions), 1)

    def test_insufficient_balance_and_invalid_price_do_not_change_balance(self):
        result = self.wallet.purchase(
            "expensive",
            "Expensive item",
            10_001,
            idempotency_key="expensive-1",
        )
        self.assertEqual(result.status, "insufficient_funds")
        with self.assertRaises(ValueError):
            self.wallet.purchase("bad", "Bad", -1, idempotency_key="bad-1")
        self.assertEqual(self.wallet.balance, 10_000)
        self.assertEqual(self.wallet.transactions, [])

    def test_save_error_does_not_mutate_wallet(self):
        with patch.object(self.wallet, "_write_state", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.wallet.purchase("normal_entry", "Normal entry", 500, idempotency_key="save-fail")
        self.assertEqual(self.wallet.balance, 10_000)
        self.assertFalse(self.wallet.has_access("normal_entry"))

    def test_malformed_save_is_logged_and_uses_starting_balance(self):
        self.save_path.write_text(json.dumps({"balance": -1}), encoding="utf-8")
        with self.assertLogs("wallet", level="ERROR"):
            loaded = Wallet(self.save_path)
        self.assertEqual(loaded.balance, 10_000)


if __name__ == "__main__":
    unittest.main()
