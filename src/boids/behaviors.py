"""Behaviors here implemented as functions taking a boid and it's neighbors and returning a Vector2 force"""

from .vector2 import Vector2

MAX_ALIGNMENT = 10

SEPARATION_STR = 100
ALIGNEMENT_STR = 1
COHESION_STR = 1


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


def sep_ali_coh(boid, neighbors):
    """Unifies separation, alignment and cohesion calculation for optimization"""

    separation = Vector2(0, 0)
    average_velocity = Vector2(0, 0)
    average_position = Vector2(0, 0)

    sensor = boid.sensor_range

    for other in neighbors:
        offset = boid.position - other.position
        distance = offset.length()

        if distance > 0:
            strength = (max(0, sensor - distance) / sensor) ** 3
            if strength > 0:
                separation += offset * (strength / distance)

        average_velocity += other.velocity
        average_position += other.position

    count = len(neighbors)
    average_velocity /= count
    average_position /= count

    alignment = average_velocity - boid.velocity
    cohesion = average_position - boid.position

    if alignment.length() > MAX_ALIGNMENT:
        alignment = alignment.normalize() * MAX_ALIGNMENT

    return (
        separation * SEPARATION_STR
        + alignment * ALIGNEMENT_STR
        + cohesion * COHESION_STR
    )


def flock(boid, neighbors):
    if not len(neighbors):
        return Vector2(0, 0)
    else:
        return sep_ali_coh(boid, neighbors)
