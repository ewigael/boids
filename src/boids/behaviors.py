"""Behaviors here implemented as functions taking a boid and it's neighbors and returning a Vector2 force"""

from .vector2 import Vector2
import numpy as np

MAX_ALIGNMENT = 10

SEPARATION_STR = 100
ALIGNEMENT_STR = 1.5
COHESION_STR = 2

AVOID_BOUNDARY_STR = 200


def avoid_boundary(boid, world_width, world_height):
    force_x = force_y = 0
    margin = 100

    if boid.position.x < margin:
        force_x = (margin - boid.position.x) / margin
    elif boid.position.x > world_width - margin:
        force_x = -(boid.position.x - (world_width - margin)) / margin
    if boid.position.y < margin:
        force_y = (margin - boid.position.y) / margin
    elif boid.position.y > world_height - margin:
        force_y = -(boid.position.y - (world_height - margin)) / margin

    return Vector2(force_x, force_y) * AVOID_BOUNDARY_STR


def sep_ali_coh_numpy(entities, neighbors):

    has_neighbors = neighbors.nb_count > 0

    # cohesion
    position_sums = np.zeros_like(entities.positions)
    np.add.at(position_sums, neighbors.sources, entities.positions[neighbors.targets])

    cohesion = np.zeros_like(entities.positions)
    cohesion[has_neighbors] = (
        position_sums[has_neighbors] / neighbors.nb_count[has_neighbors, None]
        - entities.positions[has_neighbors]
    )

    # alignement
    velocities_sums = np.zeros_like(entities.velocities)
    np.add.at(
        velocities_sums, neighbors.sources, entities.velocities[neighbors.targets]
    )

    alignement = np.zeros_like(entities.positions)
    alignement[has_neighbors] = (
        velocities_sums[has_neighbors] / neighbors.nb_count[has_neighbors, None]
        - entities.velocities[has_neighbors]
    )

    # separation
    distances = np.sqrt(neighbors.distance_squared)

    valid = distances > 0

    strength = np.zeros_like(distances)
    strength[valid] = (
        (entities.sensor_range - distances[valid]) / entities.sensor_range
    ) ** 3
    strength_over_distance = np.zeros_like(distances)
    np.divide(strength, distances, out=strength_over_distance, where=valid)

    contributions = neighbors.offsets * strength_over_distance[:, None]

    separation = np.zeros_like(entities.positions)
    np.add.at(separation, neighbors.sources, contributions)

    return separation, cohesion, alignement
