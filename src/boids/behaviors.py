"""Behaviors here implemented as functions taking a boid and it's neighbors and returning a Vector2 force"""

from .vector2 import Vector2

MAX_ALIGNMENT = 10


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


def alignment(boid, neighbors):
    average_velocity = Vector2(0, 0)

    for other in neighbors:
        average_velocity += other.velocity

    average_velocity /= len(neighbors)
    steering = average_velocity - boid.velocity

    if steering.length() > MAX_ALIGNMENT:
        return steering.normalize() * MAX_ALIGNMENT
    else:
        return steering


def flock(boid, neighbors):
    force = Vector2(0, 0)

    if not len(neighbors):
        return force

    force += separation(boid, neighbors) * 50
    force += alignment(boid, neighbors) * 2

    return force
