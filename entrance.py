"""Purchase-gated entrance and safe spawn transitions for the club doorway."""

from ursina import Entity, Vec3, color, scene
from ursina.shaders import unlit_shader


class ClubEntrance:
    OUTSIDE_SPAWN = Vec3(14, 0.05, 27.6)
    INSIDE_SPAWN = Vec3(14, 0.05, 32.0)
    DOOR_POSITION = Vec3(14, 0.05, 29.8)

    def __init__(self, player, wallet, interactions, ui, reception, audio=None):
        self.player = player
        self.wallet = wallet
        self.ui = ui
        self.reception = reception
        self.audio = audio
        self.is_inside = False

        # A visible tinted-glass panel and its collider keep the opening gated until E is used.
        self.barrier = Entity(
            parent=scene,
            model="cube",
            position=(14, 1.05, 30.25),
            scale=(5.6, 2.1, 0.08),
            color=color.rgba32(42, 105, 155, 115),
            shader=unlit_shader,
            collider="box"
        )
        for x in (13.0, 15.0):
            Entity(parent=scene, model="cube", position=(x, 1.05, 30.25),
                   scale=(0.08, 2.2, 0.12), color=color.rgb32(65, 185, 255), shader=unlit_shader)
        interactions.register(
            self.prompt,
            self.DOOR_POSITION,
            self.interact,
            radius=3.35
        )

    def prompt(self):
        if self.is_inside:
            return "Exit nightclub"
        if self.wallet.has_access("normal_entry"):
            return "Enter nightclub"
        return "Talk to reception"

    def interact(self):
        if self.is_inside:
            self.exit()
        elif self.wallet.has_access("normal_entry"):
            self.enter()
        else:
            self.reception.show()

    def enter(self):
        if not self.wallet.has_access("normal_entry"):
            self.reception.show()
            return False
        self.is_inside = True
        self.player.position = Vec3(self.INSIDE_SPAWN)
        if self.audio:
            self.audio.play_effect("door")
        self.ui.notify("Welcome inside Neon Raat strip club.")
        return True

    def exit(self):
        if not self.is_inside:
            return False
        self.is_inside = False
        self.player.position = Vec3(self.OUTSIDE_SPAWN)
        if self.audio:
            self.audio.play_effect("door")
        self.ui.notify("You are back outside.")
        return True
