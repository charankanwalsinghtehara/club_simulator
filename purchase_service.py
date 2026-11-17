"""Confirmation-first purchases shared by the reception and club vendors."""

import logging
from uuid import uuid4


logger = logging.getLogger(__name__)


class PurchaseService:
    def __init__(self, wallet, ui, audio=None):
        self.wallet = wallet
        self.ui = ui
        self.audio = audio

    def request(self, item_id, title, price, *, grants=(), on_success=None):
        grants = tuple(grants)
        if grants and all(self.wallet.has_access(key) for key in grants):
            self.ui.notify("That access is already unlocked; you were not charged.")
            if on_success:
                on_success()
            return
        transaction_id = str(uuid4())

        def confirm():
            try:
                result = self.wallet.purchase(
                    item_id,
                    title,
                    price,
                    idempotency_key=transaction_id,
                    grants=grants,
                )
            except OSError as error:
                logger.exception("Could not save purchase %s", transaction_id)
                self.ui.notify(f"Purchase not completed: save error ({error}).")
                return

            if result.status == "purchased":
                self.ui.set_wallet(result.balance)
                self.ui.notify(f"{title} purchased. Balance: INR {result.balance:,}")
                if self.audio:
                    self.audio.play_effect("purchase")
                if on_success:
                    on_success()
            elif result.status == "insufficient_funds":
                self.ui.notify(f"Insufficient balance. Cost INR {price:,}; balance INR {result.balance:,}.")
            else:
                self.ui.notify(result.message)

        self.ui.open_menu(
            "Confirm purchase",
            [
                (f"Confirm {title}  -  INR {price:,}", confirm),
                ("Cancel", lambda: self.ui.notify("Purchase cancelled.")),
            ],
            footer=f"Current balance: INR {self.wallet.balance:,}  |  Esc to cancel"
        )
