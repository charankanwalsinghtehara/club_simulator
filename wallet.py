"""Persistent, single-source-of-truth virtual wallet."""

from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path


logger = logging.getLogger(__name__)
DEFAULT_BALANCE = 10_000
HISTORY_LIMIT = 200
PRICES = {
    "normal_entry": 500,
    "vip_entry": 2_000,
    "private_lounge": 1_000,
    "dance_entertainment": 300,
    "refreshment": 200,
}


@dataclass(frozen=True)
class PurchaseResult:
    status: str
    message: str
    balance: int


class Wallet:
    def __init__(self, save_path=None, starting_balance=DEFAULT_BALANCE):
        self.save_path = Path(save_path) if save_path else Path(__file__).parent / "user_data" / "wallet.json"
        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.entitlements = set()
        self.transactions = []
        self.processed_ids = set()
        self._load()

    def _load(self):
        try:
            data = json.loads(self.save_path.read_text(encoding="utf-8"))
            balance = data["balance"]
            entitlements = data.get("entitlements", [])
            transactions = data.get("transactions", [])
            processed_ids = data.get("processed_ids", [])
            if type(balance) is not int or balance < 0:
                raise ValueError("saved wallet balance must be a non-negative integer")
            if not isinstance(entitlements, list) or not all(isinstance(item, str) for item in entitlements):
                raise ValueError("saved wallet entitlements are malformed")
            if not isinstance(transactions, list) or not all(
                isinstance(item, dict)
                and isinstance(item.get("id"), str)
                and isinstance(item.get("item_id"), str)
                and isinstance(item.get("title"), str)
                and type(item.get("amount")) is int
                and item["amount"] >= 0
                and type(item.get("balance_after")) is int
                and item["balance_after"] >= 0
                for item in transactions
            ):
                raise ValueError("saved wallet transaction history is malformed")
            if not isinstance(processed_ids, list) or not all(isinstance(item, str) for item in processed_ids):
                raise ValueError("saved wallet idempotency history is malformed")
        except FileNotFoundError:
            return
        except (OSError, ValueError, TypeError, KeyError) as error:
            logger.error("Unable to load wallet save %s: %s; using the starting balance.", self.save_path, error)
            return

        self.balance = balance
        self.entitlements = set(entitlements)
        self.transactions = transactions[-HISTORY_LIMIT:]
        self.processed_ids = set(processed_ids) | {item["id"] for item in transactions}

    def _write_state(self, balance, entitlements, transactions, processed_ids):
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.save_path.with_suffix(self.save_path.suffix + ".tmp")
        payload = {
            "version": 1,
            "balance": balance,
            "entitlements": sorted(entitlements),
            "transactions": transactions[-HISTORY_LIMIT:],
            "processed_ids": sorted(processed_ids),
        }
        try:
            temp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            os.replace(temp_path, self.save_path)
        except OSError:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError as cleanup_error:
                logger.warning("Could not remove temporary wallet file %s: %s", temp_path, cleanup_error)
            raise

    def has_access(self, entitlement):
        return entitlement in self.entitlements

    def purchase(self, item_id, title, price, *, idempotency_key, grants=()):
        if not isinstance(item_id, str) or not item_id:
            raise ValueError("item_id must be a non-empty string")
        if not isinstance(idempotency_key, str) or not idempotency_key:
            raise ValueError("idempotency_key must be a non-empty string")
        if type(price) is not int or price < 0:
            raise ValueError("price must be a non-negative integer")

        if idempotency_key in self.processed_ids:
            return PurchaseResult("duplicate", "This purchase was already processed.", self.balance)
        grants = tuple(grants)
        if grants and all(entitlement in self.entitlements for entitlement in grants):
            return PurchaseResult("already_unlocked", "This access is already unlocked.", self.balance)
        if self.balance < price:
            return PurchaseResult("insufficient_funds", "Insufficient balance.", self.balance)

        updated_entitlements = self.entitlements | set(grants)
        transaction = {
            "id": idempotency_key,
            "item_id": item_id,
            "title": title,
            "amount": price,
            "balance_after": self.balance - price,
        }
        updated_transactions = (self.transactions + [transaction])[-HISTORY_LIMIT:]
        updated_processed_ids = self.processed_ids | {idempotency_key}
        updated_balance = self.balance - price

        self._write_state(updated_balance, updated_entitlements, updated_transactions, updated_processed_ids)
        self.balance = updated_balance
        self.entitlements = updated_entitlements
        self.transactions = updated_transactions
        self.processed_ids = updated_processed_ids
        return PurchaseResult("purchased", f"{title} purchased.", self.balance)

