"""Distance-based E-key interactions for props, NPCs, and doorways."""

from dataclasses import dataclass

from ursina import Vec3


@dataclass
class Interactable:
    prompt: str
    position: object
    callback: object
    radius: float
    active: object = None


class InteractionSystem:
    def __init__(self, ui, wallet=None):
        self.ui = ui
        self.wallet = wallet
        self.interactables = []
        self.npc_systems = []
        self.target = None

    def register(self, prompt, position, callback, *, radius=2.6, active=None):
        target = Interactable(prompt, position, callback, radius, active)
        self.interactables.append(target)
        return target

    def register_npc_system(self, npc_system):
        self.npc_systems.append(npc_system)

    @staticmethod
    def _position(value):
        return value() if callable(value) else value

    def _nearest(self, player_position):
        if not isinstance(player_position, Vec3):
            player_position = Vec3(*player_position)
        candidates = []
        for item in self.interactables:
            if item.active and not item.active():
                continue
            point = self._position(item.position)
            if not isinstance(point, Vec3):
                point = Vec3(*point)
            distance = (point - player_position).length()
            if distance <= item.radius:
                candidates.append((distance, item))

        for system in self.npc_systems:
            for npc in system.npcs:
                requirement = getattr(npc, "access_requirement", None)
                if requirement and (self.wallet is None or not self.wallet.has_access(requirement)):
                    continue
                distance = (npc.position - player_position).length()
                if distance <= 2.5:
                    candidates.append((distance, npc))
        return min(candidates, key=lambda candidate: candidate[0])[1] if candidates else None

    def update(self, player_position):
        self.target = None if self.ui.menu_open else self._nearest(player_position)
        if self.target is None:
            self.ui.set_prompt("")
        elif isinstance(self.target, Interactable):
            prompt = self.target.prompt() if callable(self.target.prompt) else self.target.prompt
            self.ui.set_prompt(f"E  {prompt}")
        else:
            self.ui.set_prompt(f"E  Talk to {self.target.name} ({self.target.role})")

    def interact(self, player_position):
        if self.ui.menu_open:
            return False
        self.target = self._nearest(player_position)
        if self.target is None:
            return False
        if isinstance(self.target, Interactable):
            self.target.callback()
        else:
            self.target.interact(self.ui)
        return True
