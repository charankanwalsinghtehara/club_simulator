from ursina import *
from ursina.collider import BoxCollider
from club import create_club_exterior
from club_interior import create_club_interior
from audio_manager import AudioManager
from entrance import ClubEntrance
from interaction import InteractionSystem
from movement import move_with_collisions
from purchase_service import PurchaseService
from reception import Reception
from ui_manager import UIManager
from vip import VIPAreas
from wallet import PRICES, Wallet

app = Ursina()
window.title = 'NEON RAAT | Strip Club RP'
window.borderless = False
window.color = color.rgb32(7, 8, 18)
window.fps_counter.enabled = True

# Lighting and a dark sky make the scene readable instead of a white void.
Sky(color=color.rgb32(7, 8, 18))
AmbientLight(color=color.rgba32(125, 115, 155, 255))
sun = DirectionalLight()
sun.look_at(Vec3(1, -2, -1))

# Use solid cube geometry for the ground/road: this avoids a plane-orientation
# ambiguity and guarantees a visible floor in different Ursina versions.
ground = Entity(model='cube', position=(0, -0.25, 0), scale=(110, 0.5, 120),
                color=color.rgb32(42, 48, 54), collider='box')
road = Entity(model='cube', position=(0, 0.015, 0), scale=(12, 0.04, 110),
              color=color.rgb32(19, 20, 27))
for z in range(-50, 55, 8):
    Entity(model='cube', position=(0, 0.045, z), scale=(0.16, 0.025, 3),
           color=color.rgb32(220, 205, 150))


def create_building(x, z, height):
    Entity(model='cube', position=(x, height / 2, z), scale=(8, height, 10),
           color=color.rgb32(38, 43, 60), collider='box')
    for y in range(2, int(height), 3):
        for offset in (-2, 2):
            Entity(model='cube', position=(x + offset, y, z - 5.06),
                   scale=(1.3, 1.2, 0.08), color=color.rgb32(255, 177, 75))

for z in range(-35, 45, 15):
    create_building(-15, z, 12)
    if z == 25:
        create_building(31, z, 18)
    elif z != 40:
        create_building(15, z, 18)

create_club_exterior()
club_interior = create_club_interior()

# Player placeholder is deliberately a visible low-poly character, not a flat
# blue panel. All gameplay NPCs are adult-coded background characters.
player = Entity(position=(0, 0.05, -15), rotation_y=0)
player.collider = BoxCollider(player, center=(0, 0.9, 0), size=(0.8, 1.8, 0.6))
Entity(parent=player, model='cube', position=(0, 0.9, 0), scale=(0.62, 1.0, 0.38),
       color=color.rgb32(35, 105, 190))
Entity(parent=player, model='sphere', position=(0, 1.62, 0), scale=0.38,
       color=color.rgb32(190, 145, 115))
Entity(parent=player, model='cube', position=(-0.19, 0.25, 0), scale=(0.18, 0.5, 0.2),
       color=color.rgb32(20, 24, 35))
Entity(parent=player, model='cube', position=(0.19, 0.25, 0), scale=(0.18, 0.5, 0.2),
       color=color.rgb32(20, 24, 35))

camera.fov = 82
camera.position = player.position + Vec3(0, 5, -9)
camera.look_at(player.position + Vec3(0, 1, 0))
camera_inside = False

speed = 7
wallet = Wallet()
ui = UIManager()
ui.set_wallet(wallet.balance)
audio = AudioManager()
ui.sound_callback = lambda: audio.play_effect("ui")
purchases = PurchaseService(wallet, ui, audio)
interactions = InteractionSystem(ui, wallet)
interactions.register_npc_system(club_interior.npcs)

reception = Reception(ui, purchases, club_interior.npcs)
entrance = ClubEntrance(player, wallet, interactions, ui, reception, audio)
reception.set_entrance(entrance)
vip_areas = VIPAreas(
    wallet,
    purchases,
    interactions,
    club_interior.npcs,
    inside_check=lambda: entrance.is_inside,
    audio=audio
)
reception.set_access_updater(vip_areas.update_access)

bartender = next(npc for npc in club_interior.npcs.npcs if npc.role == "Bartender")
performer = next(npc for npc in club_interior.npcs.npcs if npc.role == "Dancer")


def open_bar_menu(npc):
    ui.open_menu(
        "NEON RAAT  |  STRIP CLUB BAR",
        [
            (
                f"Buy refreshments  -  INR {PRICES['refreshment']:,}",
                lambda: purchases.request("refreshment", "Refreshments", PRICES["refreshment"])
            ),
            ("Talk to Ravi", lambda: ui.show_dialogue(npc.name, npc.next_dialogue())),
            ("Close", lambda: None),
        ],
        footer="E to interact  |  Esc to close"
    )


def open_stage_menu(npc):
    ui.open_menu(
        "NEON RAAT  |  STAGE SHOW",
        [
            (
                f"Request dance entertainment  -  INR {PRICES['dance_entertainment']:,}",
                lambda: purchases.request(
                    "dance_entertainment",
                    "Dance entertainment",
                    PRICES["dance_entertainment"]
                )
            ),
            ("Talk to Mira", lambda: ui.show_dialogue(npc.name, npc.next_dialogue())),
            ("Close", lambda: None),
        ],
        footer="Performances are non-explicit  |  Esc to close"
    )


bartender.interact_callback = open_bar_menu
performer.interact_callback = open_stage_menu


def show_transaction_history():
    transactions = wallet.transactions[-8:]
    options = [
        (
            f"{item['title']}  -  INR {item['amount']:,}  |  balance INR {item['balance_after']:,}",
            lambda: None
        )
        for item in reversed(transactions)
    ] or [("No purchases recorded yet.", lambda: None)]
    options.append(("Close", lambda: None))
    ui.open_menu("WALLET TRANSACTIONS", options, footer=f"Current balance: INR {wallet.balance:,}")


def input(key):
    if ui.handle_key(key):
        return
    if key == 'escape':
        application.quit()
    elif key == 'e':
        if not interactions.interact(player.position):
            ui.notify("Nothing to interact with nearby.")
    elif key == 'm':
        audio.open_settings(ui)
    elif key == 'h':
        show_transaction_history()


def update():
    global camera_inside

    if not ui.menu_open:
        direction = Vec3(0, 0, 0)
        if held_keys['w']:
            direction.z += 1
        if held_keys['s']:
            direction.z -= 1
        if held_keys['a']:
            direction.x -= 1
        if held_keys['d']:
            direction.x += 1
        if direction.length() > 0:
            direction = direction.normalized()
            movement_speed = speed * 1.55 if held_keys['shift'] else speed
            movement = direction * movement_speed * time.dt
            move_with_collisions(player, movement)

    if entrance.is_inside:
        camera_offset = Vec3(0, 4.0, -1.2)
        target = player.position + Vec3(0, 1.35, 3.2)
    else:
        camera_offset = Vec3(0, 5, -9)
        target = player.position + Vec3(0, 1, 0)

    desired_camera = player.position + camera_offset
    if camera_inside != entrance.is_inside:
        camera.position = desired_camera
        camera_inside = entrance.is_inside
    else:
        camera.position = lerp(camera.position, desired_camera, min(1, time.dt * 5))
    camera.look_at(target)
    interactions.update(player.position)
    ui.update(time.dt)
    club_interior.update(time.dt, player.position)

app.run()
