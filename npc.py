"""Reusable procedural adult NPCs and lightweight behaviors."""

import math
import random

from ursina import Entity, Vec3, color, scene


class NPC:
    def __init__(
        self, name, role, position, outfit, accent, *, behavior="idle",
        dialogue=(), waypoints=(), interact_callback=None
    ):
        self.name = name
        self.role = role
        self.age = random.randint(21, 42)
        self.behavior = behavior
        self.dialogue = tuple(dialogue) or (f"{name}: Welcome to Neon Raat.",)
        self._dialogue_index = 0
        self.waypoints = [Vec3(*point) for point in waypoints]
        self.waypoint_index = 0
        self.interact_callback = interact_callback
        self.dance_style = random.randrange(3)
        self.phase = random.random() * math.tau
        self.focus_position = None
        self.root = Entity(parent=scene, position=position)
        self.base_position = Vec3(*position)

        self.torso = Entity(parent=self.root, model="cube", position=(0, 0.88, 0),
                            scale=(0.5, 0.92, 0.32), color=outfit)
        self.head = Entity(parent=self.root, model="sphere", position=(0, 1.58, 0),
                           scale=0.34, color=color.rgb32(185, 137, 108))
        Entity(parent=self.root, model="sphere", position=(0, 1.73, 0.015),
               scale=(0.35, 0.16, 0.35), color=color.rgb32(30, 22, 24))
        self.legs = []
        for x in (-0.16, 0.16):
            leg = Entity(parent=self.root, model="cube", position=(x, 0.25, 0),
                         scale=(0.17, 0.5, 0.2), color=color.rgb32(25, 24, 34))
            self.legs.append(leg)
        self.arms = []
        for x in (-0.36, 0.36):
            arm = Entity(parent=self.root, model="cube", position=(x, 1.0, 0),
                         scale=(0.16, 0.68, 0.18), color=outfit)
            Entity(parent=arm, model="cube", position=(0, -0.3, -0.01),
                   scale=(1.03, 0.16, 1.04), color=accent)
            self.arms.append(arm)
        self.stage_costume = []
        if role == "Dancer":
            self.stage_costume.extend((
                Entity(parent=self.root, model="cube", position=(0, 1.12, -0.01),
                       scale=(0.52, 0.18, 0.34), color=accent),
                Entity(parent=self.root, model="cube", position=(0, 0.48, -0.01),
                       scale=(0.53, 0.18, 0.35), color=accent),
            ))
            for leg in self.legs:
                self.stage_costume.append(
                    Entity(parent=self.root, model="cube", position=leg.position + Vec3(0, -0.16, 0),
                           scale=(0.19, 0.18, 0.23), color=color.rgb32(24, 21, 33))
                )
        self.set_behavior(behavior)

    @property
    def position(self):
        return self.root.position

    def set_behavior(self, behavior, waypoints=None):
        if behavior not in {"idle", "walk", "dance", "pole_dance", "sit", "watch"}:
            raise ValueError(f"Unknown NPC behavior: {behavior}")
        self.behavior = behavior
        if waypoints is not None:
            self.waypoints = [Vec3(*point) for point in waypoints]
            self.waypoint_index = 0
        sitting = behavior == "sit"
        self.torso.y = 0.72 if sitting else 0.88
        self.head.y = 1.36 if sitting else 1.58
        for leg in self.legs:
            leg.rotation_x = 72 if sitting else 0
            leg.y = 0.28 if sitting else 0.25

    def next_dialogue(self):
        line = self.dialogue[self._dialogue_index % len(self.dialogue)]
        self._dialogue_index += 1
        return line

    def interact(self, ui):
        if self.interact_callback:
            self.interact_callback(self)
            return
        ui.show_dialogue(self.name, self.next_dialogue())

    def update(self, dt, player_position=None):
        self.phase += dt
        if player_position is not None and not isinstance(player_position, Vec3):
            player_position = Vec3(*player_position)
        if self.behavior == "walk" and self.waypoints:
            target = self.waypoints[self.waypoint_index]
            delta = target - self.root.position
            delta.y = 0
            if delta.length() < 0.18:
                self.waypoint_index = (self.waypoint_index + 1) % len(self.waypoints)
            elif delta.length() > 0:
                direction = delta.normalized()
                self.root.position += direction * min(1.05 * dt, delta.length())
                self.root.rotation_y = math.degrees(math.atan2(direction.x, direction.z))
        elif self.behavior == "dance":
            phase = self.phase * (2.1 + self.dance_style * 0.35)
            self.torso.rotation_z = math.sin(phase) * (4 + self.dance_style * 2)
            self.root.rotation_y = math.sin(phase * 0.65) * 13
            amplitude = (22, 34, 28)[self.dance_style]
            self.arms[0].rotation_z = -18 - math.sin(phase) * amplitude
            self.arms[1].rotation_z = 18 + math.sin(phase + 1.1) * amplitude
        elif self.behavior == "pole_dance":
            phase = self.phase * (1.45 + self.dance_style * 0.12)
            sway = math.sin(phase)
            self.root.y = self.base_position.y + 0.04 * math.sin(phase * 2)
            self.root.rotation_y = math.sin(phase * 0.45) * 24
            self.torso.rotation_z = sway * 5
            self.arms[0].rotation_z = -62 - sway * 9
            self.arms[1].rotation_z = 62 + math.sin(phase + 0.9) * 9
            self.legs[0].rotation_z = sway * 5
            self.legs[1].rotation_z = -sway * 5
        else:
            self.torso.rotation_z = math.sin(self.phase * 1.1) * 1.8
            self.arms[0].rotation_z = -4 + math.sin(self.phase) * 3
            self.arms[1].rotation_z = 4 - math.sin(self.phase + 0.5) * 3

        if player_position is not None and (player_position - self.position).length() < 5:
            direction = player_position - self.position
            self.head.rotation_y = math.degrees(math.atan2(direction.x, direction.z)) - self.root.rotation_y
        elif self.behavior == "watch" and self.focus_position is not None:
            direction = self.focus_position - self.position
            self.root.rotation_y = math.degrees(math.atan2(direction.x, direction.z))
            self.head.rotation_y = 0
        else:
            self.head.rotation_y = 0


class NPCSystem:
    def __init__(self):
        self.npcs = []
        self._update_accumulator = 0.0

    def spawn(self, name, role, position, outfit, accent, **kwargs):
        npc = NPC(name, role, position, outfit, accent, **kwargs)
        self.npcs.append(npc)
        return npc

    def update(self, dt, player_position=None):
        self._update_accumulator += dt
        if self._update_accumulator < 0.05:
            return
        elapsed = self._update_accumulator
        self._update_accumulator = 0.0
        for npc in self.npcs:
            npc.update(elapsed, player_position)
