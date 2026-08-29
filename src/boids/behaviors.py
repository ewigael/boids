"""Behaviors here implemented as functions taking a boid and it's neighbors and returning a Vector2 force"""

import numpy as np

from .config import config
from .vector2 import Vector2


def avoid_boundary(entities):
    force = np.zeros_like(entities.positions)
    margin = config.behaviors.boundary.margin
    exp_factor = config.behaviors.boundary.exp_factor
    world_width = config.world.width
    world_height = config.world.height

    x = entities.positions[:, 0]
    y = entities.positions[:, 1]

    too_left = x < margin
    too_right = x > world_width - margin
    too_up = y < margin
    too_down = y > world_height - margin

    force[too_left, 0] = ((margin - x[too_left]) / margin) ** exp_factor
    force[too_right, 0] = -(
        ((x[too_right] - (world_width - margin)) / margin) ** exp_factor
    )
    force[too_up, 1] = ((margin - y[too_up]) / margin) ** exp_factor
    force[too_down, 1] = -(
        ((y[too_down] - (world_height - margin)) / margin) ** exp_factor
    )

    return force * config.behaviors.boundary.strength


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

    # alignment
    velocities_sums = np.zeros_like(entities.velocities)
    np.add.at(
        velocities_sums, neighbors.sources, entities.velocities[neighbors.targets]
    )

    alignment = np.zeros_like(entities.positions)
    alignment[has_neighbors] = (
        velocities_sums[has_neighbors] / neighbors.nb_count[has_neighbors, None]
        - entities.velocities[has_neighbors]
    )

    # separation
    distances = np.sqrt(neighbors.distance_squared)

    valid = distances > 0

    strength = np.zeros_like(distances)
    strength[valid] = (
        (entities.sensor_range - distances[valid]) / entities.sensor_range
    ) ** config.behaviors.separation.exp_factor
    strength_over_distance = np.zeros_like(distances)
    np.divide(strength, distances, out=strength_over_distance, where=valid)

    contributions = neighbors.offsets * strength_over_distance[:, None]

    separation = np.zeros_like(entities.positions)
    np.add.at(separation, neighbors.sources, contributions)

    return (
        separation * config.behaviors.separation.strength,
        cohesion * config.behaviors.cohesion.strength,
        alignment * config.behaviors.alignment.strength,
    )
