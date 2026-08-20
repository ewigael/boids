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

        strength = (max(0, boid.sensor_range - distance) / boid.sensor_range) ** 3
        steering += offset * (strength / distance)

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


def cohesion(boid, neighbors):

    average_position = Vector2(0, 0)

    for other in neighbors:
        average_position += other.position

    average_position /= len(neighbors)

    steering = average_position - boid.position

    return steering


def flock(boid, neighbors):
    force = Vector2(0, 0)

    if not len(neighbors):
        return force

    force += separation(boid, neighbors) * 100
    force += alignment(boid, neighbors) * 1
    force += cohesion(boid, neighbors) * 1

    return force
