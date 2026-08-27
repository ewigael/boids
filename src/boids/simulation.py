"""Simulation class"""

from random import randint
import pygame
import numpy as np
from perflogger import PerfLogger

from .boid import Boid
from .behaviors import flock, avoid_boundary
from .vector2 import Vector2

from .colors import small_change_hex


class Entities:

    # TODO: Add speed table, would aboid resqrting everything for drawing

    initial_speed = 100

    min_speed = 70
    max_speed = 150

    sensor_range = 60

    def __init__(self, gamestate, count, width, height):

        species_color = "#AA712F"
        self.gamestate = gamestate

        if not gamestate["quiet"]:
            print(f"> generating entities ({count})")

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
        self.colors = [small_change_hex(species_color) for _ in range(0, count)]

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


class SpatialGrid:
    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.cells = {}

    def get_cell(self, position):
        x, y = position
        return (x // self.cell_size, y // self.cell_size)

    def add(self, boid):
        cell = self.get_cell(boid.position)
        if cell not in self.cells:
            self.cells[cell] = []
        self.cells[cell].append(boid)

    def rebuild(self, boids):
        self.cells.clear()
        for b in boids:
            self.add(b)

    def get_local_agents(self, target, search_range=1):
        """Return a list of all agents in neighboring cells, searching a square of size search_range * 2 + 1"""
        agents = []
        cell_x, cell_y = self.get_cell(target)

        for dx in range(-search_range, search_range + 1):
            for dy in range(-search_range, search_range + 1):
                cell = (cell_x + dx, cell_y + dy)
                if cell in self.cells:
                    agents.extend(self.cells[cell])

        return agents

    def iter_local_agents(self, target, search_range=1):
        """Iterative version of get_local_agents"""
        cell_x, cell_y = self.get_cell(target)

        for dx in range(-search_range, search_range + 1):
            for dy in range(-search_range, search_range + 1):
                cell = (cell_x + dx, cell_y + dy)
                if cell in self.cells:
                    yield from self.cells[cell]


class Simulation:

    def __init__(self, game_state, width, height, boids_count, load_save=None):
        if not game_state.state["quiet"]:
            print("Initialising Simulation...")
        self.gamestate = game_state.state

        self.entities = Entities(self.gamestate, boids_count, width, height)
        self.width = width
        self.height = height

        self.nb_mask = None

        # if load_save:
        #     if not game_state.state["quiet"]:
        #         print("> Loading from file")

        #         # loading entities
        #         self.boids = []
        #         for boid in load_save["boids"]:
        #             boid_o = Boid(
        #                 name=boid["name"],
        #                 species=boid["species"],
        #                 color=boid["color"],
        #                 x=boid["position"][0],
        #                 y=boid["position"][1],
        #                 velocity=Vector2(boid["velocity"][0], boid["velocity"][1]),
        #                 acceleration=Vector2(
        #                     boid["acceleration"][0], boid["acceleration"][1]
        #                 ),
        #             )
        #             self.boids.append(boid_o)
        #             if isinstance(game_state.state["focus"], dict):
        #                 if (
        #                     boid["name"] == game_state.state["focus"]["name"]
        #                     and boid["species"] == game_state.state["focus"]["species"]
        #                 ):
        #                     game_state.state["focus"] = boid_o

        #         self.width = int(load_save["world"][0])
        #         self.height = int(load_save["world"][1])

        # else:
        #     self.width = width
        #     self.height = height

        #     self.boids = [
        #         Boid(name=str(i + 1), x=randint(0, width - 1), y=randint(0, height - 1))
        #         for i in range(0, boids_count)
        #     ]

        #     self.game_state.state["boids_count"] = boids_count

        # self.grid = SpatialGrid(60)
        # self.grid.rebuild(self.boids)

        self.perflog = PerfLogger("Simulation", avgs_step=0.5)

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

    def get_neighbors(self, bid):
        if self.nb_mask is not None:
            return np.flatnonzero(self.nb_mask[bid])
        else:
            return []

    def get_neighbors_entities(self):

        offsets = (
            self.entities.positions[:, None, :] - self.entities.positions[None, :, :]
        )
        distance_squared = np.sum(offsets**2, axis=2)

        neighbor_mask = distance_squared < self.entities.sensor_range**2
        np.fill_diagonal(neighbor_mask, False)

        return neighbor_mask, neighbor_mask.sum(axis=1)

    def update_entities(self, dt):

        if self.gamestate["sim_paused"]:
            return

        self.perflog.start()

        # TODO: grid rebuild

        # GET NEIGHBORS ####
        offsets = (
            self.entities.positions[:, None, :] - self.entities.positions[None, :, :]
        )
        distance_squared = np.sum(offsets**2, axis=2)

        nb_mask = distance_squared < self.entities.sensor_range**2
        np.fill_diagonal(nb_mask, False)

        nb_count = nb_mask.sum(axis=1)
        self.nb_mask = nb_mask

        self.perflog.add("get_neighbors")

        # FORCES ####

        has_neighbors = nb_count > 0

        # cohesion
        position_sums = nb_mask @ self.entities.positions
        cohesion = np.zeros_like(self.entities.positions)
        cohesion[has_neighbors] = (
            position_sums[has_neighbors] / nb_count[has_neighbors, None]
            - self.entities.positions[has_neighbors]
        )

        # alignement
        velocities_sums = nb_mask @ self.entities.velocities
        alignement = np.zeros_like(self.entities.positions)
        alignement[has_neighbors] = (
            velocities_sums[has_neighbors] / nb_count[has_neighbors, None]
            - self.entities.velocities[has_neighbors]
        )

        # separation
        distances = np.sqrt(distance_squared)
        strength = (
            (self.entities.sensor_range - distances) / self.entities.sensor_range
        ) ** 3
        valid = nb_mask & (distances > 0)
        strength_over_distance = np.zeros_like(distances)
        np.divide(strength, distances, out=strength_over_distance, where=valid)
        contributions = offsets * strength_over_distance[..., None]
        contributions[~valid] = 0
        separation = np.sum(contributions, axis=1)

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
