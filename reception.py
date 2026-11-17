"""Reception desk and confirmation menus for club entry packages."""

from ursina import Entity, color, scene

from wallet import PRICES


class Reception:
    def __init__(self, ui, purchases, npc_system):
        self.ui = ui
        self.purchases = purchases
        self.entrance = None
        self.access_updater = None
        desk = Entity(
            parent=scene,
            model="cube",
            position=(16.35, 0.62, 32.5),
            scale=(1.35, 1.15, 0.9),
            color=color.rgb32(48, 30, 55),
            collider="box"
        )
        Entity(parent=scene, model="cube", position=(16.35, 1.22, 32.5),
               scale=(1.5, 0.1, 0.98), color=color.rgb32(255, 192, 96), unlit=True)
        receptionist = npc_system.spawn(
            "Anaya", "Receptionist", (16.35, 0.05, 33.55),
            color.rgb32(50, 90, 130), color.rgb32(255, 192, 96),
            behavior="idle",
            dialogue=("Welcome to Neon Raat strip club. Choose an entry package at reception.",),
            interact_callback=lambda _npc: self.show()
        )
        receptionist.root.rotation_y = 180

    def set_entrance(self, entrance):
        self.entrance = entrance

    def set_access_updater(self, callback):
        self.access_updater = callback

    def _after_access_purchase(self):
        if self.access_updater:
            self.access_updater()
        if self.entrance:
            self.entrance.enter()

    def show(self):
        options = (
            ("Normal entry  -  INR 500", "normal_entry", PRICES["normal_entry"], ("normal_entry",)),
            ("VIP entry  -  INR 2,000", "vip_entry", PRICES["vip_entry"], ("normal_entry", "vip_entry")),
            ("Private lounge  -  INR 1,000", "private_lounge", PRICES["private_lounge"],
             ("normal_entry", "private_lounge")),
        )
        self.ui.open_menu(
            "NEON RAAT  |  RECEPTION",
            [
                (
                    label,
                    lambda item_id=item_id, label=label, price=price, grants=grants:
                        self.purchases.request(
                            item_id,
                            label.split("  -")[0],
                            price,
                            grants=grants,
                            on_success=self._after_access_purchase,
                        ),
                )
                for label, item_id, price, grants in options
            ] + [("Close", lambda: None)],
            footer="Select an entry package  |  Esc to close"
        )
