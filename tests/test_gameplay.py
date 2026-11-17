import tempfile
import unittest
from pathlib import Path

from ursina import Entity, Ursina, Vec3, color
from ursina.collider import BoxCollider

from entrance import ClubEntrance
from interaction import InteractionSystem
from movement import move_with_collisions
from npc import NPCSystem
from purchase_service import PurchaseService
from reception import Reception
from ui_manager import UIManager
from vip import VIPAreas
from wallet import PRICES, Wallet


class GameplayFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Ursina(window_type="offscreen", development_mode=False, editor_ui_enabled=False)

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.wallet = Wallet(Path(self.temp_dir.name) / "wallet.json")
        self.ui = UIManager()
        self.ui.set_wallet(self.wallet.balance)
        self.interactions = InteractionSystem(self.ui, self.wallet)
        self.npcs = NPCSystem()
        self.interactions.register_npc_system(self.npcs)
        self.purchases = PurchaseService(self.wallet, self.ui)
        self.reception = Reception(self.ui, self.purchases, self.npcs)
        self.player = type("Player", (), {})()
        self.player.position = Vec3(0, 0.05, -15)
        self.entrance = ClubEntrance(
            self.player, self.wallet, self.interactions, self.ui, self.reception
        )
        self.reception.set_entrance(self.entrance)
        self.vip = VIPAreas(
            self.wallet, self.purchases, self.interactions, self.npcs,
            inside_check=lambda: self.entrance.is_inside
        )
        self.reception.set_access_updater(self.vip.update_access)
        self.addCleanup(self.ui.close_menu)

    def test_normal_entry_confirmation_and_exit(self):
        self.assertEqual(self.wallet.balance, 10_000)
        self.assertIsNotNone(self.entrance.barrier.collider)
        self.assertTrue(self.interactions.interact(self.entrance.DOOR_POSITION))
        self.assertTrue(self.ui.menu_open)
        self.ui.choose(0)
        self.ui.choose(0)
        self.assertEqual(self.wallet.balance, 9_500)
        self.assertTrue(self.entrance.is_inside)
        self.assertEqual(self.player.position, Vec3(self.entrance.INSIDE_SPAWN))
        self.assertTrue(self.interactions.interact(self.entrance.INSIDE_SPAWN))
        self.assertEqual(self.player.position, Vec3(self.entrance.OUTSIDE_SPAWN))
        self.reception.show()
        self.ui.choose(0)
        self.assertTrue(self.entrance.is_inside)
        self.assertEqual(self.wallet.balance, 9_500)

    def test_vip_purchase_unlocks_gate_and_never_charges_twice(self):
        self.reception.show()
        self.ui.choose(1)
        self.ui.choose(0)
        self.assertEqual(self.wallet.balance, 8_000)
        self.assertIsNone(self.vip.gates["vip"][0].collider)
        self.assertTrue(self.entrance.is_inside)

    def test_vip_gate_purchase_unlocks_and_duplicate_request_is_free(self):
        self.vip._request_access(
            "VIP lounge",
            "vip_entry",
            PRICES["vip_entry"],
            ("normal_entry", "vip_entry"),
        )
        self.ui.choose(0)
        self.assertEqual(self.wallet.balance, 8_000)
        self.assertIsNone(self.vip.gates["vip"][0].collider)
        self.vip._request_access(
            "VIP lounge",
            "vip_entry",
            PRICES["vip_entry"],
            ("normal_entry", "vip_entry"),
        )
        self.assertFalse(self.ui.menu_open)
        self.assertEqual(self.wallet.balance, 8_000)

    def test_interaction_prompt_and_insufficient_funds(self):
        self.interactions.update(self.entrance.DOOR_POSITION)
        self.assertEqual(self.ui.prompt.text, "E  Talk to reception")
        self.wallet.balance = 100
        self.purchases.request("refreshment", "Refreshments", PRICES["refreshment"])
        self.ui.choose(0)
        self.assertEqual(self.wallet.balance, 100)
        self.assertIn("Insufficient balance", self.ui.toast.text)

    def test_escape_closes_modal_without_quitting_flow(self):
        self.reception.show()
        self.assertTrue(self.ui.handle_key("escape"))
        self.assertFalse(self.ui.menu_open)

    def test_substepped_movement_stops_at_thin_door_barrier(self):
        wall = Entity(model="cube", position=(0, 1, 0.25), scale=(4, 2, 0.08), collider="box")
        player = Entity(position=(0, 0.05, -0.5))
        player.collider = BoxCollider(player, center=(0, 0.9, 0), size=(0.8, 1.8, 0.6))
        move_with_collisions(player, Vec3(0, 0, 1.4))
        self.assertLess(player.z, wall.z - 0.3)

    def test_pole_dancers_are_adults_and_have_a_looping_stage_pose(self):
        performer = self.npcs.spawn(
            "Mira", "Dancer", (19, 0.52, 42.7),
            outfit=color.rgb32(130, 43, 87),
            accent=color.rgb32(255, 192, 96),
            behavior="pole_dance",
        )
        self.assertGreaterEqual(performer.age, 18)
        initial_pose = (performer.arms[0].rotation_z, performer.arms[1].rotation_z)
        performer.update(0.2)
        self.assertNotEqual(
            (performer.arms[0].rotation_z, performer.arms[1].rotation_z),
            initial_pose,
        )


if __name__ == "__main__":
    unittest.main()
