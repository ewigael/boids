"""Simulation class"""

from random import randint
import pygame

from .boid import Boid
from .behaviors import flock
from .perflog import PerformanceLogger


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

    def __init__(self, game_state, width, height, boids_count):
        print("Initialising Simulation...")
        self.game_state = game_state
        self.width = width
        self.height = height

        self.boids = [
            Boid(randint(0, width - 1), randint(0, height - 1))
            for _ in range(0, boids_count)
        ]
        self.game_state.state["boids_count"] = boids_count

        self.grid = SpatialGrid(60)
        self.grid.rebuild(self.boids)

        self.perflog = PerformanceLogger("Simulation", avgs_step=0.5)

    def get_neighbors(self, boid):
        neighbors = []

        for other in self.grid.iter_local_agents(boid.position):
            if boid is other:
                continue
            elif boid.is_in_range(other):
                neighbors.append(other)

        return neighbors

    def update(self, dt):

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
