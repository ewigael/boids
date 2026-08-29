"""Simulation class"""

import numpy as np

from perflogger import PerfLogger

from .grid import SpatialGrid
from .entities import Entities
from .neighbors import NeighborsData

from .behaviors import sep_ali_coh_numpy


class Simulation:

    def __init__(self, game_state, width, height, boids_count, load_save=None):
        if not game_state.state["quiet"]:
            print("Initialising Simulation...")
        self.gamestate = game_state.state

        if load_save:
            self.width = int(load_save["world"][0])
            self.height = int(load_save["world"][1])
            self.entities = Entities(self.gamestate, load_save=load_save)
        else:
            self.entities = Entities(self.gamestate, boids_count, width, height)
            self.width = width
            self.height = height

        self.grid = SpatialGrid(60, self.width, self.height)
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

        separation, cohesion, alignement = sep_ali_coh_numpy(
            self.entities, self.neighbors
        )

        # control
        if self.gamestate["focus"] is not None:
            bid = self.gamestate["focus"]
            force = np.zeros(2)
            if self.gamestate["focus_boid_go_direction"] is not None:
                force += (
                    self.gamestate["focus_boid_go_direction"] * 2
                    - self.entities.velocities[bid]
                )
            if self.gamestate["focus_boid_go_faster"]:
                force += self.entities.velocities[bid] * 1.1
            if self.gamestate["focus_boid_go_slower"]:
                force -= self.entities.velocities[bid] * 1.1
            self.entities.accelerations[bid] += force

        self.entities.accelerations += separation * 100 + alignement * 1.5 + cohesion

        self.perflog.add("calc forces")

        # UPDATE
        self.entities.update_all(dt)

        self.perflog.add("entities_updates")

        # WRAP
        self.wrap_entities()

    def wrap_entities(self):
        self.entities.positions %= np.array([(self.width, self.height)])
