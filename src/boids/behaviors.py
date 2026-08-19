"""Behaviors here implemented as functions taking a boid and it's neighbors and returning a Vector2 force"""

from .vector2 import Vector2


def separation(boid, neighbors):
    steering = Vector2(0, 0)

    for other in neighbors:
        offset = boid.position - other.position
        distance = offset.length()
        if distance == 0:
            continue

        strength = (max(0, boid.sensor_range - distance) / boid.sensor_range) ** 2
        steering += offset.normalize() * strength

    return steering


def flock(boid, neighbors):
    force = Vector2(0, 0)

    if not len(neighbors):
        return force

    force += separation(boid, neighbors) * 100

    return force
