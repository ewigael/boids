"""Simulation class"""

import numpy as np

from perflogger import PerfLogger

from .config import config
from .grid import SpatialGrid
from .entities import Entities
from .neighbors import NeighborsData

from .behaviors import sep_ali_coh_numpy, avoid_boundary


class Simulation:

    def __init__(self, game_state, width, height, boids_count, load_save=None):
        if not game_state.state["quiet"]:
            print("Initialising Simulation...")
        self.gamestate = game_state.state

        if load_save:
            self.entities = Entities(self.gamestate, load_save=load_save)
        else:
            self.entities = Entities(self.gamestate, boids_count, width, height)

        self.grid = SpatialGrid(60, config.world.width, config.world.height)
        self.grid.rebuild(self.entities)

        self.neighbors = NeighborsData(self.entities)

        self.perflog = PerfLogger("Simulation", avgs_step=0.5)

    @property
    def neighbors_ready(self):
        return all(
            x is not None
            for x in (
                self.neighbors.candidates_sources,
                self.neighbors.candidates_targets,
                self.neighbors.sources,
                self.neighbors.targets,
            )
        )

    def get_candidates(self, bid):
        candidate_mask = self.neighbors.candidates_sources == bid
        return self.neighbors.candidates_targets[candidate_mask].tolist()

    def get_neighbors(self, bid):
        neighbor_mask = self.neighbors.sources == bid
        return self.neighbors.targets[neighbor_mask].tolist()

    def find_boid_at(self, target, _range=20):
        """Find the closest boid to target within range"""

        delta = self.entities.positions - target
        distance_squared = np.sum(delta**2, axis=1)
        within_range = distance_squared < _range**2

        if not np.any(within_range):
            return None

        candidates = np.where(within_range)[0]
        closest = candidates[np.argmin(distance_squared[within_range])]

        return closest

    def update_entities(self, dt):

        if self.gamestate["sim_paused"]:
            return

        self.perflog.start()

        # GET CANDITATES ####

        self.grid.rebuild(self.entities)
        self.perflog.add("grid_rebuild")
        candidates_sources, candidates_targets = self.grid.get_candidate_pairs()
        self.perflog.add("get_candidate_pairs")

        # GET NEIGHBORS ####
        self.neighbors.rebuild(candidates_sources, candidates_targets)
        self.perflog.add("rebuild_neighbors")

        # FORCES ####

        # Flocking
        separation, cohesion, alignement = sep_ali_coh_numpy(
            self.entities, self.neighbors
        )
        self.entities.accelerations += separation + alignement + cohesion
        self.perflog.add("calc sep ali coh")

        # Avoid boundary
        if self.gamestate["boids_avoid_boundary"]:
            self.entities.accelerations += avoid_boundary(self.entities)
            self.perflog.add("calc avoid boundary")

        # Control
        if self.gamestate["focus"] is not None:
            bid = self.gamestate["focus"]
            force = np.zeros(2)
            if self.gamestate["focus_boid_go_direction"] is not None:
                force += (
                    self.gamestate["focus_boid_go_direction"] * 3.5
                    - self.entities.velocities[bid]
                )
            if self.gamestate["focus_boid_go_faster"]:
                force += self.entities.velocities[bid] * 1.1
            if self.gamestate["focus_boid_go_slower"]:
                force -= self.entities.velocities[bid] * 1.1
            self.entities.accelerations[bid] += force
            self.perflog.add("calc control")

        # UPDATE
        self.entities.update_all(dt)

        self.perflog.add("entities_updates")

        # WRAP
        self.wrap_entities()

    def wrap_entities(self):
        self.entities.positions %= np.array([(config.world.width, config.world.height)])
