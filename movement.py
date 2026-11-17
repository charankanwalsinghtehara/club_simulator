"""Axis-separated movement with bounded collision substeps to prevent tunneling."""

import math

from ursina import Vec3


MAX_COLLISION_STEP = 0.18


def move_with_collisions(entity, displacement):
    """Move an entity on X/Z while stopping at colliders, including thin doors."""
    for axis_delta in (
        Vec3(displacement.x, 0, 0),
        Vec3(0, 0, displacement.z),
    ):
        distance = axis_delta.length()
        if distance == 0:
            continue
        step_count = max(1, math.ceil(distance / MAX_COLLISION_STEP))
        step = axis_delta / step_count
        for _ in range(step_count):
            entity.position += step
            if entity.intersects().hit:
                entity.position -= step
                break
