
"""Neon Raat - Premium strip-club exterior
Stage 2: Original Indian adult nightlife venue environment.
"""

from ursina import Entity, Text, color, scene
from ursina.shaders import unlit_shader


def box(position, scale, tint, collider=None):
    return Entity(
        model="cube",
        position=position,
        scale=scale,
        color=tint,
        shader=unlit_shader,
        collider=collider
    )


def create_person(position, outfit, accent):
    """Low-poly adult NPC placeholder."""
    x, y, z = position

    box((x, y + 0.8, z), (0.6, 1.5, 0.4), outfit, "box")
    for offset in (-0.18, 0.18):
        box((x + offset, y + 0.22, z), (0.18, 0.45, 0.22), color.rgb32(20, 20, 28))
        box((x + offset * 1.8, y + 0.85, z), (0.16, 0.75, 0.18), outfit)

    Entity(
        model="sphere",
        position=(x, y + 1.55, z),
        scale=0.35,
        color=color.rgb32(190, 145, 112),
        shader=unlit_shader
    )

    box((x, y + 0.9, z - 0.21), (0.12, 0.5, 0.04), accent)


def create_car(position, body_color, glass_color):
    """Create an original low-poly parked car with a blocking body collider."""
    x, y, z = position
    box((x, y + 0.55, z), (2, 0.75, 3.5), body_color, "box")
    box((x, y + 1.02, z - 0.12), (1.55, 0.42, 1.72), glass_color)
    box((x, y + 0.95, z + 1.72), (1.5, 0.12, 0.08), color.rgb32(255, 215, 125))
    box((x, y + 0.9, z - 1.77), (1.5, 0.12, 0.08), color.rgb32(230, 45, 70))

    for wx in (x - 0.88, x + 0.88):
        for wz in (z - 1.1, z + 1.1):
            Entity(
                model="sphere",
                position=(wx, y + 0.32, wz),
                scale=(0.24, 0.42, 0.42),
                color=color.rgb32(12, 12, 18),
                shader=unlit_shader
            )


def create_club_exterior():

    # Club position
    cx = 14
    cz = 40
    front = 30.0

    # Colors
    black = color.rgb32(12, 10, 22)
    purple = color.rgb32(180, 45, 255)
    red = color.rgb32(255, 35, 85)
    blue = color.rgb32(40, 160, 255)
    gold = color.rgb32(255, 190, 90)
    wall = color.rgb32(40, 27, 57)
    glass = color.rgb32(25, 55, 85)

    # --------------------------------
    # BUILDING STRUCTURE
    # --------------------------------

    # Back wall
    box(
        (cx, 6, 49),
        (16, 12, 0.5),
        wall,
        "box"
    )

    # Left and right walls
    box(
        (6.25, 6, cz),
        (0.5, 12, 18),
        wall,
        "box"
    )

    box(
        (21.75, 6, cz),
        (0.5, 12, 18),
        wall,
        "box"
    )

    # Front wall split into two sections.
    # Central entrance remains physically open.
    box(
        (8.5, 6, front),
        (5, 12, 0.5),
        wall,
        "box"
    )

    box(
        (19.5, 6, front),
        (5, 12, 0.5),
        wall,
        "box"
    )

    # Top front beam
    box(
        (14, 11.5, front),
        (6, 1, 0.5),
        wall
    )

    # Roof
    box(
        (14, 12.1, 40),
        (16, 0.4, 19),
        black
    )

    # --------------------------------
    # ENTRANCE
    # --------------------------------

    # Door frames
    box((11.5, 5, 29.8), (0.15, 10, 0.2), blue)
    box((16.5, 5, 29.8), (0.15, 10, 0.2), blue)

    # Open glass door leaves leave a clear central passage into the building.
    box((12.25, 4, 29.95), (1.5, 8, 0.08), glass)
    box((15.75, 4, 29.95), (1.5, 8, 0.08), glass)

    # Door handles
    box((13.05, 4, 29.85), (0.06, 1, 0.06), gold)
    box((14.95, 4, 29.85), (0.06, 1, 0.06), gold)

    # Neon entrance frame
    box((14, 9.2, 29.7), (5.2, 0.15, 0.2), purple)
    box((11.4, 5, 29.7), (0.15, 8.5, 0.2), purple)
    box((16.6, 5, 29.7), (0.15, 8.5, 0.2), purple)

    # --------------------------------
    # NIGHTCLUB SIGN
    # --------------------------------

    box(
        (14, 10.5, 29.65),
        (9, 2.3, 0.25),
        black
    )

    Text(
        "NEON RAAT",
        parent=scene,
        position=(11.4, 10.15, 29.45),
        rotation=(0, 180, 0),
        scale=1.5,
        color=purple
    )

    Text(
        "LUXE STRIP CLUB",
        parent=scene,
        position=(11.9, 9.0, 29.45),
        rotation=(0, 180, 0),
        scale=0.4,
        color=gold
    )

    # --------------------------------
    # FRONT WINDOWS
    # --------------------------------

    for x in (7.5, 9.3, 18.7, 20.5):

        for y in (3.5, 7):

            box(
                (x, y, 29.7),
                (1.4, 2.2, 0.08),
                glass
            )

            box(
                (x, y + 1.15, 29.65),
                (1.5, 0.08, 0.08),
                blue
            )

    # --------------------------------
    # NEON ARCHITECTURE
    # --------------------------------

    box((14, 1, 29.55), (15, 0.12, 0.12), red)
    box((14, 12.4, 30), (15, 0.12, 0.12), purple)

    box((6, 6, 39), (0.12, 10, 17), blue)
    box((22, 6, 39), (0.12, 10, 17), red)

    # Side decorative lights
    for z in (34, 39, 44):

        box(
            (6.5, 7, z),
            (0.1, 2, 1.5),
            glass
        )

        box(
            (6.4, 8.1, z),
            (0.1, 0.1, 1.7),
            purple
        )

    # --------------------------------
    # ENTRANCE CANOPY
    # --------------------------------

    box(
        (14, 8, 27.5),
        (7.5, 0.3, 4),
        black
    )

    for x in (10.5, 17.5):

        box(
            (x, 4, 27.5),
            (0.2, 8, 0.2),
            purple
        )

    # --------------------------------
    # PARKING AREA
    # --------------------------------

    box(
        (14, 0.03, 24),
        (18, 0.05, 10),
        color.rgb32(35, 32, 43)
    )

    for x in (7, 10, 18, 21):

        box(
            (x, 0.07, 24),
            (0.1, 0.04, 5),
            gold
        )

    box((14, 0.07, 21.5), (15, 0.04, 0.1), gold)
    box((14, 0.07, 26.5), (15, 0.04, 0.1), gold)

    # Parked original procedural vehicles.
    create_car((8.5, 0, 24), color.rgb32(40, 75, 130), glass)
    create_car((19.5, 0, 24), color.rgb32(110, 35, 75), glass)

    # --------------------------------
    # SECURITY AND CUSTOMERS
    # --------------------------------

    create_person(
        (10.2, 0, 29),
        color.rgb32(25, 25, 35),
        blue
    )

    create_person(
        (17.8, 0, 29),
        color.rgb32(25, 25, 35),
        red
    )

    create_person(
        (19.5, 0, 28),
        color.rgb32(85, 35, 80),
        gold
    )

    print("Neon Raat exterior created successfully.")
