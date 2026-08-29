"""Simulation class"""

from random import randint
import pygame
import numpy as np
from perflogger import PerfLogger

from .boid import Boid
from .behaviors import sep_ali_coh_numpy
from .vector2 import Vector2

from .colors import small_change_hex


class Entities:

    initial_speed = 100

    min_speed = 70
    max_speed = 150

    sensor_range = 60
    sensor_range_squared = sensor_range**2

    def __init__(self, gamestate, count=0, width=0, height=0, load_save=None):

        # self.species_color = "#F0C580"  # gold
        # self.species_color = "#FF00EE"  # super pink
        self.species_color = "#F080E9"  # pink
        self.gamestate = gamestate

        if not gamestate["quiet"]:
            print(f"> Generating entities ({count})")

        if load_save:
            self.load_from_save(load_save)
            return

        self.width = width
        self.height = height

        self.count = count
        self.gamestate["boids_count"] = count

        self.positions = np.random.randint(0, [width, height], size=(count, 2)).astype(
            np.float32
        )

        angles = np.random.uniform(0, 2 * np.pi, size=count)
        self.velocities = (
            np.column_stack(
                (
                    np.cos(angles),
                    np.sin(angles),
                )
            )
            * self.initial_speed
        )
        self.speeds = np.linalg.norm(self.velocities, axis=1)
        self.accelerations = np.zeros((count, 2), dtype=np.float32)
        self.colors = [small_change_hex(self.species_color) for _ in range(0, count)]

    def update_all(self, dt):
        """Update all entities, taking advantage of numpy"""

        # Applying accelerations
        self.velocities += self.accelerations * dt
        self.accelerations.fill(0)

        # Clamping speeds
        speed_squared = np.sum(self.velocities**2, axis=1)

        too_slow = speed_squared < self.min_speed**2
        too_fast = speed_squared > self.max_speed**2

        # TODO: Remove unnecessary square roots
        speeds = np.sqrt(speed_squared)

        self.velocities[too_slow] *= self.min_speed / speeds[too_slow, None]
        self.velocities[too_fast] *= self.max_speed / speeds[too_fast, None]

        # Updating positions
        self.positions += self.velocities * dt
        self.speeds = np.linalg.norm(self.velocities, axis=1)

    def add(self, n):
        for _ in range(0, n):
            self.positions = np.vstack(
                [
                    self.positions,
                    np.random.randint(0, [self.width, self.height], size=(1, 2)).astype(
                        np.float32
                    ),
                ]
            )
            self.velocities = np.vstack(
                [
                    self.velocities,
                    np.random.randint(0, [self.width, self.height], size=(1, 2)).astype(
                        np.float32
                    ),
                ]
            )
            self.accelerations = np.vstack([self.accelerations, np.zeros(2)])
            self.colors.append(small_change_hex(self.species_color))

            self.count += 1
        self.gamestate["boids_count"] = self.count

    def remove(self, n):
        for _ in range(0, n):
            self.positions = np.delete(self.positions, -1, axis=0)
            self.velocities = np.delete(self.velocities, -1, axis=0)
            self.accelerations = np.delete(self.accelerations, -1, axis=0)
            self.colors.pop()

            self.count -= 1
        self.gamestate["boids_count"] = self.count

    def to_list(self):
        """Returns a list version of Entities data, to be used for serialization"""
        return {
            "count": self.count,
            "positions": self.positions.tolist(),
            "velocities": self.velocities.tolist(),
            "speeds": self.speeds.tolist(),
            "accelerations": self.accelerations.tolist(),
            "colors": self.colors,
        }

    def load_from_save(self, load_save):
        self.width = load_save["world"]["width"]
        self.height = load_save["world"]["height"]
        self.count = load_save["entities"]["count"]
        self.positions = np.array(load_save["entities"]["positions"], dtype=np.float32)
        self.velocities = np.array(
            load_save["entities"]["velocities"], dtype=np.float32
        )
        self.speeds = np.array(load_save["entities"]["speeds"], dtype=np.float32)
        self.accelerations = np.array(
            load_save["entities"]["accelerations"], dtype=np.float32
        )
        self.colors = load_save["entities"]["colors"]


class SpatialGrid:
    def __init__(self, cell_size, width, height):
        self.cell_size = cell_size
        self.cells = {}
        self.width = width
        self.height = height

        self.cols = int(np.ceil(width / cell_size))
        self.rows = int(np.ceil(height / cell_size))

        self.cells = [[] for _ in range(self.cols * self.rows)]

    def cell_index(self, position):
        x = int(position[0] // self.cell_size)
        y = int(position[1] // self.cell_size)

        return y * self.cols + x

    def rebuild(self, entities):
        cell_xy = (entities.positions // self.cell_size).astype(np.intp)
        cell_indices = cell_xy[:, 1] * self.cols + cell_xy[:, 0]

        self.sorted_boids = np.argsort(cell_indices, kind="quicksort")

        self.sorted_cells = cell_indices[self.sorted_boids]

        self.cell_counts = np.bincount(
            self.sorted_cells,
            minlength=self.cols * self.rows,
        )

        self.cell_starts = np.cumsum(self.cell_counts) - self.cell_counts

    def get_neighbor_cells(self, cell_index):
        x = cell_index % self.cols
        y = cell_index // self.cols

        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx = x + dx
                ny = y + dy

                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    yield ny * self.cols + nx

    def get_candidate_pairs(self):
        sources = []
        targets = []

        for ci in np.flatnonzero(self.cell_counts):
            start = self.cell_starts[ci]
            end = start + self.cell_counts[ci]
            cell = self.sorted_boids[start:end]

            # this cell's pairs
            if len(cell) > 1:
                i, j = np.triu_indices(len(cell), k=1)
                a = cell[i]
                b = cell[j]

                sources.append(np.concatenate([a, b]))
                targets.append(np.concatenate([b, a]))

            # neighbor cells pairs
            for ni in self.get_neighbor_cells(ci):
                if self.cell_counts[ni] == 0:
                    continue
                if ni <= ci:
                    continue

                start = self.cell_starts[ni]
                end = start + self.cell_counts[ni]
                neighbors = self.sorted_boids[start:end]

                if len(cell) == 0 or len(neighbors) == 0:
                    continue

                a, b = np.meshgrid(cell, neighbors, indexing="ij")

                a = a.ravel()
                b = b.ravel()

                sources.append(np.concatenate([a, b]))
                targets.append(np.concatenate([b, a]))

        return (
            np.concatenate(sources),
            np.concatenate(targets),
        )


class NeighborsData:
    def __init__(self, entities):

        self.entities = entities

        self.nb_mask = None
        self.sources = None
        self.targets = None
        self.candidates_sources = None
        self.candidates_targets = None
        self.offsets = None
        self.distance_squared = None
        self.nb_count = None

    def rebuild(self, candidates_sources, candidates_targets):

        self.candidates_sources = candidates_sources
        self.candidates_targets = candidates_targets

        offsets = (
            self.entities.positions[self.candidates_sources]
            - self.entities.positions[self.candidates_targets]
        )
        distance_squared = np.sum(offsets**2, axis=1)
        valid = distance_squared < self.entities.sensor_range_squared

        self.sources = self.candidates_sources[valid]
        self.targets = self.candidates_targets[valid]

        self.offsets = offsets[valid]
        self.distance_squared = distance_squared[valid]

        self.nb_count = np.bincount(
            self.sources,
            minlength=self.entities.count,
        )


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
