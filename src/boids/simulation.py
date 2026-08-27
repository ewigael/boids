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

    initial_speed = 100

    def __init__(self, gamestate, count, width, height):

        species_color = "#FFC927"
        self.gamestate = gamestate

        if not gamestate["quiet"]:
            print(f"> generating entities ({count})")

        self.count = count

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

        self.accelerations = np.zeros((count, 2), dtype=np.float32)

        self.colors = [small_change_hex(species_color) for _ in range(0, count)]


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
        self.game_state = game_state

        self.entities = Entities(game_state.state, boids_count, width, height)

        if load_save:
            if not game_state.state["quiet"]:
                print("> Loading from file")

                # loading entities
                self.boids = []
                for boid in load_save["boids"]:
                    boid_o = Boid(
                        name=boid["name"],
                        species=boid["species"],
                        color=boid["color"],
                        x=boid["position"][0],
                        y=boid["position"][1],
                        velocity=Vector2(boid["velocity"][0], boid["velocity"][1]),
                        acceleration=Vector2(
                            boid["acceleration"][0], boid["acceleration"][1]
                        ),
                    )
                    self.boids.append(boid_o)
                    if isinstance(game_state.state["focus"], dict):
                        if (
                            boid["name"] == game_state.state["focus"]["name"]
                            and boid["species"] == game_state.state["focus"]["species"]
                        ):
                            game_state.state["focus"] = boid_o

                self.width = int(load_save["world"][0])
                self.height = int(load_save["world"][1])

        else:
            self.width = width
            self.height = height

            self.boids = [
                Boid(name=str(i + 1), x=randint(0, width - 1), y=randint(0, height - 1))
                for i in range(0, boids_count)
            ]

            self.game_state.state["boids_count"] = boids_count

        self.grid = SpatialGrid(60)
        self.grid.rebuild(self.boids)

        self.perflog = PerfLogger("Simulation", avgs_step=0.5)

    def get_neighbors(self, boid):
        """Return a list of neighboring boids within passed boid's sensor range"""
        neighbors = []

        for other in self.grid.iter_local_agents(boid.position):
            if boid is other:
                continue
            elif boid.is_in_range(other):
                neighbors.append(other)

        return neighbors

    def find_boid_at(self, target, _range=20):
        """Find the closest boid to target within range"""
        closest = None
        clo_dis_sqr = _range**2

        for candidate in self.grid.iter_local_agents(target):
            can_dis_sqr = (candidate.position.x - target.x) ** 2 + (
                candidate.position.y - target.y
            ) ** 2
            if can_dis_sqr < clo_dis_sqr:
                closest = candidate
                clo_dis_sqr = can_dis_sqr

        return closest

    def update(self, dt):
        """Rebuild the spatial grid, list all neighbors
        and run through all boids to apply their behavior
        before updating all boids
        """

        self.perflog.start()

        if self.game_state.state["sim_paused"]:
            return

        self.grid.rebuild(self.boids)
        self.perflog.add("grid rebuild")

        neighbor_list = []

        for boid in self.boids:
            neighbor_list.append(self.get_neighbors(boid))
        self.perflog.add("update neighbors listing")

        for boid, neighbors in zip(self.boids, neighbor_list):
            force = flock(boid, neighbors)
            force += avoid_boundary(boid, self.width, self.height)

            if boid == self.game_state.state["focus"]:
                if self.game_state.state["focus_boid_go_direction"]:
                    force = self.game_state.state[
                        "focus_boid_go_direction"
                    ] - boid.velocity * (dt / 2)
                if self.game_state.state["focus_boid_go_faster"]:
                    force += boid.velocity * 1.1
                if self.game_state.state["focus_boid_go_slower"]:
                    force -= boid.velocity * 1.1
            boid.apply_force(force)
        self.perflog.add("boids compute")

        for boid in self.boids:
            boid.update(dt)
        self.perflog.add("boids update")

        self.wrap_boids()
        self.perflog.add("boids wrap")

    def wrap_boids(self):

        for boid in self.boids:
            boid.position.x %= self.width
            boid.position.y %= self.height
