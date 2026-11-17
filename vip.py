"""Purchase-gated VIP lounge and private-room partitions."""

from ursina import Entity, Vec3, color, scene
from ursina.shaders import unlit_shader

from wallet import PRICES


def _prop(position, scale, tint, collider=None, *, glow=False):
    return Entity(
        parent=scene,
        model="cube",
        position=position,
        scale=scale,
        color=tint,
        shader=unlit_shader if glow else None,
        collider=collider
    )


class VIPAreas:
    def __init__(self, wallet, purchases, interactions, npc_system, inside_check, audio=None):
        self.wallet = wallet
        self.purchases = purchases
        self.interactions = interactions
        self.npc_system = npc_system
        self.inside_check = inside_check
        self.audio = audio
        self.gates = {}

        self._build_partition(
            "vip",
            x=17.8,
            left_z=32.5,
            right_z=36.5,
            entitlement="vip_entry",
            label="VIP lounge",
            item_id="vip_entry",
            price=PRICES["vip_entry"],
            grants=("normal_entry", "vip_entry"),
            tint=color.rgb32(205, 87, 255)
        )
        self._build_partition(
            "private",
            x=10.2,
            left_z=32.5,
            right_z=36.5,
            entitlement="private_lounge",
            label="Private lounge",
            item_id="private_lounge",
            price=PRICES["private_lounge"],
            grants=("normal_entry", "private_lounge"),
            tint=color.rgb32(255, 195, 106)
        )

        # A compact private lounge sits clear of the bar aisle and front entrance.
        _prop((8.35, 0.4, 36.0), (2.55, 0.7, 0.9), color.rgb32(73, 34, 73), "box")
        _prop((8.35, 0.94, 36.33), (2.55, 0.46, 0.25), color.rgb32(198, 72, 245), glow=True)
        _prop((9.35, 0.55, 36.9), (0.9, 0.12, 0.9), color.rgb32(255, 192, 96), "box", glow=True)
        _prop((9.35, 0.28, 36.9), (0.12, 0.48, 0.12), color.rgb32(28, 20, 32), "box")
        _prop((7.4, 0.38, 36.9), (0.75, 0.6, 0.75), color.rgb32(52, 50, 75), "box")
        self.private_guest = npc_system.spawn(
            "Ira", "VIP Guest", (8.35, 0.4, 36.0),
            color.rgb32(91, 48, 102), color.rgb32(255, 188, 100),
            behavior="sit", dialogue=("This private lounge is lovely.",)
        )
        self.private_guest.access_requirement = "private_lounge"

        self.vip_guest = npc_system.spawn(
            "Rehan", "VIP Guest", (19.65, 0.05, 38.3),
            color.rgb32(40, 78, 115), color.rgb32(190, 90, 255),
            behavior="idle", dialogue=("The VIP lounge has a great view.",)
        )
        self.vip_guest.access_requirement = "vip_entry"
        self.update_access()

    def _build_partition(self, key, *, x, left_z, right_z, entitlement, label, item_id, price, grants, tint):
        wall_color = color.rgb32(31, 24, 44)
        if key == "vip":
            room_edge = 21.5
        else:
            room_edge = 6.5
        room_center_x = (x + room_edge) / 2
        room_width = abs(room_edge - x)
        rear_z = 39.5 if key == "vip" else 37.5
        side_start_z = right_z - 1.0
        _prop((room_center_x, 5.4, rear_z), (room_width, 10.8, 0.14), wall_color, "box")
        _prop((room_center_x, 10.8, rear_z), (room_width, 0.12, 0.19), tint, glow=True)
        _prop((x, 5.4, (side_start_z + rear_z) / 2), (0.14, 10.8, rear_z - side_start_z),
              wall_color, "box")
        _prop((x, 10.8, (side_start_z + rear_z) / 2), (0.19, 0.12, rear_z - side_start_z),
              tint, glow=True)
        _prop((x, 5.4, left_z), (0.14, 10.8, 2.0), wall_color, "box")
        _prop((x, 10.8, left_z), (0.19, 0.12, 2.0), tint, glow=True)
        _prop((x, 10.85, 34.5), (0.16, 0.18, 2.0), wall_color, "box")
        gate = Entity(
            parent=scene,
            model="cube",
            position=(x, 1.05, 34.5),
            scale=(0.12, 2.1, 2.0),
            color=color.rgba32(tint[0] * 255, tint[1] * 255, tint[2] * 255, 130),
            shader=unlit_shader,
            collider="box"
        )
        self.gates[key] = (gate, entitlement)
        self.interactions.register(
            f"Unlock {label}",
            Vec3(x, 0.05, 34.5),
            lambda: self._request_access(label, item_id, price, grants),
            radius=2.8,
            active=lambda entitlement=entitlement:
                self.inside_check() and not self.wallet.has_access(entitlement)
        )

    def _request_access(self, label, item_id, price, grants):
        if self.wallet.has_access(grants[-1]):
            self.update_access()
            self.ui_message(f"{label} access is already unlocked.")
            return
        self.purchases.request(
            item_id,
            f"{label} access",
            price,
            grants=grants,
            on_success=self._access_purchased
        )

    def _access_purchased(self):
        self.update_access()
        if self.audio:
            self.audio.play_effect("door")

    def ui_message(self, message):
        self.purchases.ui.notify(message)

    def update_access(self):
        for gate, entitlement in self.gates.values():
            unlocked = self.wallet.has_access(entitlement)
            gate.collider = None if unlocked else "box"
            gate.alpha = 0.12 if unlocked else 0.48

