"""Behaviors here implemented as functions taking a boid and it's neighbors and returning a Vector2 force"""

from .vector2 import Vector2
import numpy as np

MAX_ALIGNMENT = 10

SEPARATION_STR = 100
ALIGNEMENT_STR = 1.5
COHESION_STR = 2

AVOID_BOUNDARY_STR = 400
AVOID_BOUNDARY_MARGIN = 200


def avoid_boundary(entities):
    force = np.zeros_like(entities.positions)
    margin = AVOID_BOUNDARY_MARGIN

    x = entities.positions[:, 0]
    y = entities.positions[:, 1]

    too_left = x < margin
    too_right = x > entities.width - margin
    too_up = y < margin
    too_down = y > entities.height - margin

    force[too_left, 0] = ((margin - x[too_left]) / margin) ** 2
    force[too_right, 0] = -(((x[too_right] - (entities.width - margin)) / margin) ** 2)
    force[too_up, 1] = ((margin - y[too_up]) / margin) ** 2
    force[too_down, 1] = -(((y[too_down] - (entities.height - margin)) / margin) ** 2)

    return force * AVOID_BOUNDARY_STR


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

    return (
        separation * SEPARATION_STR,
        cohesion * COHESION_STR,
        alignement * ALIGNEMENT_STR,
    )
