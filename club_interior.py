from ursina import Entity, PointLight, Text, Vec3, color, scene
from ursina.shaders import unlit_shader

from npc import NPCSystem


def _box(position, scale, tint, *, glow=False, collider=None, **kwargs):
    return Entity(
        parent=scene,
        model="cube",
        position=position,
        scale=scale,
        color=tint,
        shader=unlit_shader if glow else None,
        collider=collider,
        **kwargs
    )


class ClubInteriorEffects:
    def __init__(self, floor_tiles, npc_system, lights):
        self.floor_tiles = floor_tiles
        self.npcs = npc_system
        self.lights = lights
        self.elapsed = 0.0
        self.last_tile_update = 0.0

    def update(self, dt, player_position=None):
        self.elapsed += dt
        self.npcs.update(dt, player_position)

        if self.elapsed - self.last_tile_update < 0.18:
            return
        self.last_tile_update = self.elapsed
        palette = (
            color.rgb32(38, 15, 82),
            color.rgb32(18, 54, 100),
            color.rgb32(92, 18, 67),
            color.rgb32(25, 82, 90),
        )
        phase = int(self.elapsed * 2.2)
        for index, tile in enumerate(self.floor_tiles):
            tile.color = palette[(index + phase) % len(palette)]

        hue = (self.elapsed * 34) % 360
        self.lights[0].color = color.hsv(hue, 0.56, 0.38)
        self.lights[1].color = color.hsv((hue + 145) % 360, 0.56, 0.38)


def create_club_interior():
    ink = color.rgb32(13, 11, 25)
    wall = color.rgb32(30, 22, 43)
    purple = color.rgb32(190, 62, 255)
    blue = color.rgb32(55, 183, 255)
    pink = color.rgb32(255, 54, 145)
    gold = color.rgb32(255, 192, 96)
    glass = color.rgba32(26, 73, 103, 105)
    npcs = NPCSystem()

    # This floor sits just above the city ground and leaves the existing doorway open.
    _box((14, 0.025, 40), (15.2, 0.05, 18), color.rgb32(22, 20, 32))
    _box((14, 11.68, 40), (15.4, 0.12, 18.2), ink)

    # Interior wall facing and glass-toned decorative panels follow the existing shell.
    _box((14, 5.8, 48.72), (15.2, 11.2, 0.08), wall)
    _box((6.82, 5.8, 40), (0.08, 11.2, 16.8), wall)
    _box((21.18, 5.8, 40), (0.08, 11.2, 16.8), wall)
    for z in (34, 39, 44):
        _box((6.9, 5.2, z), (0.06, 3.1, 2.5), glass, glow=True)
        _box((21.1, 5.2, z), (0.06, 3.1, 2.5), glass, glow=True)
        _box((6.86, 7.0, z), (0.08, 0.1, 2.65), blue, glow=True)
        _box((21.14, 7.0, z), (0.08, 0.1, 2.65), pink, glow=True)

    # Perimeter strips and ceiling trusses establish the club's purple/blue/gold theme.
    _box((14, 10.7, 31.2), (14.8, 0.14, 0.12), purple, glow=True)
    _box((14, 10.7, 48.7), (14.8, 0.14, 0.12), blue, glow=True)
    for x in (8, 20):
        _box((x, 10.65, 40), (0.12, 0.12, 16.8), pink, glow=True)
    for z in (34, 39, 44):
        _box((14, 10.95, z), (13.8, 0.12, 0.16), gold, glow=True)
        for x in (10, 14, 18):
            _box((x, 10.55, z), (0.65, 0.16, 0.65), blue if x == 14 else purple, glow=True)

    # Central tiled dance floor; tiles are animated by the small effects controller.
    _box((14, 0.09, 38), (7.8, 0.08, 8.0), color.rgb32(11, 12, 24))
    floor_tiles = []
    tile_colors = (purple, blue, pink, gold)
    for row in range(4):
        for column in range(4):
            floor_tiles.append(_box(
                (11.15 + column * 1.85, 0.16, 34.8 + row * 2.12),
                (1.7, 0.055, 1.96),
                tile_colors[(row + column) % len(tile_colors)],
                glow=True
            ))
    for x in (10.25, 17.75):
        _box((x, 0.16, 38), (0.12, 0.07, 8.5), gold, glow=True)
    for z in (33.7, 42.3):
        _box((14, 0.16, z), (8.3, 0.07, 0.12), gold, glow=True)

    # DJ booth, equipment, speakers, and a backlit original club display.
    _box((14, 5.8, 48.55), (9.6, 4.7, 0.14), color.rgb32(13, 20, 45), glow=True)
    _box((14, 5.8, 48.42), (8.8, 3.8, 0.08), color.rgb32(36, 33, 99), glow=True)
    Text("NEON RAAT", parent=scene, position=(11.65, 6.15, 48.31),
         rotation=(0, 180, 0), scale=1.1, color=blue)
    Text("STRIP CLUB", parent=scene, position=(12.55, 5.35, 48.30),
         rotation=(0, 180, 0), scale=0.45, color=gold)
    Text("VIP LOUNGE", parent=scene, position=(12.7, 4.85, 48.30),
         rotation=(0, 180, 0), scale=0.3, color=pink)
    _box((14, 0.72, 46.25), (6.6, 1.25, 0.95), ink, collider="box")
    _box((14, 1.36, 46.22), (6.8, 0.1, 1.0), purple, glow=True)
    for x in (12.2, 13.1, 14.0, 14.9, 15.8):
        _box((x, 1.43, 46.12), (0.52, 0.05, 0.52), blue if x != 14 else pink, glow=True)
    for x in (10.0, 18.0):
        _box((x, 1.55, 46.25), (1.2, 3.1, 1.0), ink, collider="box")
        for y in (0.9, 2.0):
            _box((x, y, 45.72), (0.55, 0.55, 0.12), blue, glow=True)
        _box((x, 3.2, 46.25), (1.1, 0.12, 0.8), pink, glow=True)
    dj = npcs.spawn(
        "DJ Arjun", "DJ", (14, 0.05, 47.15), color.rgb32(46, 34, 87), blue,
        behavior="idle", dialogue=("The next set is dedicated to the dance floor.",)
    )
    dj.root.rotation_y = 180

    # Raised side stage and simple, non-explicit performer with decorative poles.
    _box((19.0, 0.26, 42.7), (3.5, 0.42, 4.4), color.rgb32(39, 20, 49), collider="box")
    _box((19.0, 0.5, 42.7), (3.4, 0.08, 4.3), pink, glow=True)
    _box((20.92, 5.4, 42.7), (0.12, 9.5, 5.7), color.rgb32(40, 20, 63), glow=True)
    for z in (40.4, 42.7, 45.0):
        _box((20.82, 5.2, z), (0.1, 0.12, 1.8), purple, glow=True)
    for x in (17.85, 20.15):
        _box((x, 3.15, 42.7), (0.12, 5.2, 0.12), gold, glow=True)
        _box((x, 0.57, 42.7), (0.38, 0.08, 0.38), gold, glow=True)
    for x in (17.4, 20.6):
        _box((x, 7.2, 42.7), (0.26, 0.26, 0.26), pink if x > 19 else purple, glow=True)
    npcs.spawn(
        "Mira", "Dancer", (19.0, 0.52, 42.7), color.rgb32(130, 43, 87), gold,
        behavior="pole_dance", dialogue=("Thanks for watching. Enjoy the show.")
    )
    npcs.spawn(
        "Leena", "Dancer", (20.15, 0.52, 42.7), color.rgb32(88, 42, 126), pink,
        behavior="pole_dance", dialogue=("Welcome to the main stage.")
    )
    for x, tint in ((17.2, blue), (20.8, purple)):
        _box((x, 8.7, 42.7), (0.32, 0.32, 0.32), tint, glow=True)

    # Premium bar along the left wall, with backlit shelves and stools.
    _box((8.05, 0.68, 40.3), (0.92, 1.25, 6.1), color.rgb32(47, 28, 48), collider="box")
    _box((8.05, 1.34, 40.3), (1.12, 0.12, 6.25), gold, glow=True)
    for y in (2.7, 3.8, 4.9):
        _box((7.12, y, 40.3), (0.28, 0.12, 5.8), color.rgb32(73, 42, 59), collider="box")
        _box((7.27, y + 0.34, 40.3), (0.07, 0.06, 5.75), blue, glow=True)
        for z in (38.1, 39.2, 40.3, 41.4, 42.5):
            bottle = color.rgb32(50, 180, 195) if int(z * 10) % 2 else color.rgb32(220, 65, 123)
            _box((7.2, y + 0.28, z), (0.22, 0.48, 0.22), bottle, glow=True)
            _box((7.2, y + 0.56, z), (0.12, 0.12, 0.12), gold, glow=True)
    for z in (38.1, 40.3, 42.5):
        _box((9.55, 0.72, z), (0.62, 0.12, 0.62), gold, glow=True)
        _box((9.55, 0.38, z), (0.12, 0.58, 0.12), ink, collider="box")
    bartender = npcs.spawn(
        "Ravi", "Bartender", (8.92, 0.05, 40.3), color.rgb32(25, 72, 82), gold,
        behavior="idle", dialogue=("Welcome to the bar.", "Enjoy the music!")
    )
    bartender.root.rotation_y = -90

    # Lounge seating with tables, chairs, plants, and warm accent lamps near the entry.
    for x, z in ((19.65, 36.0), (19.65, 37.6)):
        _box((x, 0.42, z), (3.0, 0.72, 0.92), color.rgb32(62, 29, 63), collider="box")
        _box((x, 0.95, z + 0.32), (3.0, 0.5, 0.28), purple, glow=True)
    _box((13.5, 0.55, 44.25), (1.15, 0.12, 1.0), gold, glow=True, collider="box")
    _box((13.5, 0.28, 44.25), (0.12, 0.48, 0.12), ink, collider="box")
    for x, z in ((12.0, 44.0), (15.0, 44.0)):
        _box((x, 0.38, z), (0.8, 0.62, 0.82), color.rgb32(46, 42, 67), collider="box")
        _box((x, 0.77, z), (0.82, 0.18, 0.82), blue, glow=True)
    for x, z in ((7.45, 32.6), (20.55, 32.6), (7.45, 47.0)):
        _box((x, 0.35, z), (0.72, 0.7, 0.72), color.rgb32(43, 31, 40))
        for dx, dz, height in ((0, 0, 1.25), (-0.22, 0.05, 0.95), (0.2, -0.1, 1.05)):
            Entity(parent=scene, model="sphere", position=(x + dx, 0.8 + height / 2, z + dz),
                   scale=(0.42, height, 0.42), color=color.rgb32(39, 117, 78))
        _box((x, 1.6, z), (0.18, 0.18, 0.18), gold, glow=True)
    npcs.spawn(
        "Asha", "Customer", (12.0, 0.05, 36.0), color.rgb32(45, 84, 125), pink,
        behavior="dance", dialogue=("This dance floor is great!")
    )
    npcs.spawn(
        "Kabir", "Customer", (15.2, 0.05, 38.1), color.rgb32(119, 49, 91), blue,
        behavior="dance", dialogue=("The DJ has a great set tonight.")
    )
    watcher = npcs.spawn(
        "Dev", "Customer", (18.1, 0.05, 40.2), color.rgb32(48, 104, 85), gold,
        behavior="watch", dialogue=("The stage show is fun.")
    )
    watcher.focus_position = Vec3(19.0, 1.0, 42.7)
    npcs.spawn(
        "Piya", "Customer", (12.0, 0.05, 40.4), color.rgb32(121, 76, 43), blue,
        behavior="walk",
        waypoints=((10.0, 0.05, 40.4), (10.0, 0.05, 43.5), (12.0, 0.05, 43.5)),
        dialogue=("I'm heading back to the dance floor.",)
    )
    lounge_guest = npcs.spawn(
        "Nisha", "Customer", (19.65, 0.4, 36.0), color.rgb32(99, 55, 96), pink,
        behavior="sit", dialogue=("I'm enjoying the lounge tonight.")
    )
    lounge_guest.access_requirement = "vip_entry"

    # Two restrained point lights add colored spill without a costly light rig.
    lights = [
        PointLight(parent=scene, position=(10.2, 6.3, 38.3), color=color.rgb32(100, 54, 150)),
        PointLight(parent=scene, position=(18.0, 6.0, 40.8), color=color.rgb32(45, 95, 155)),
    ]
    return ClubInteriorEffects(floor_tiles, npcs, lights)
