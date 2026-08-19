"""Simulation class"""

from random import randint
import pygame

from .boid import Boid
from .behaviors import flock


class SpatialGrid:
    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.cells = {}

    def get_cell(self, position):
        return (position.x // self.cell_size, position.y // self.cell_size)

    def add(self, boid):
        cell = self.get_cell(boid.position)
        if cell not in self.cells:
            self.cells[cell] = []
        self.cells[cell].append(boid)

    def rebuild(self, boids):
        self.cells.clear()
        for b in boids:
            self.add(b)

    def get_local_agents(self, boid, search_range=1):
        """Return a list of all agents in neighboring cells, searching a square of size search_range * 2 + 1"""
        agents = []
        cell_x, cell_y = self.get_cell(boid.position)

        for dx in range(-search_range, search_range + 1):
            for dy in range(-search_range, search_range + 1):
                cell = (cell_x + dx, cell_y + dy)
                if cell in self.cells:
                    agents.extend(self.cells[cell])

        return agents


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

    def get_neighbors(self, boid):

        candidates = self.grid.get_local_agents(boid)

        neighbors = []

        for other in candidates:
            if boid is other:
                continue
            elif (boid.position - other.position).length() < boid.sensor_range:
                neighbors.append(other)

        return neighbors

    def update(self, dt):

        t_start = pygame.time.get_ticks()

        if self.game_state.state["sim_paused"]:
            return

        self.grid.rebuild(self.boids)

        t_grid_rebuild = pygame.time.get_ticks()

        neighbor_list = []

        for boid in self.boids:
            neighbor_list.append(self.get_neighbors(boid))

        t_sim_update_neighbors_listing = pygame.time.get_ticks()

        for boid, neighbors in zip(self.boids, neighbor_list):
            force = flock(boid, neighbors)
            boid.apply_force(force)

        t_boids_compute = pygame.time.get_ticks()

        for boid in self.boids:
            boid.update(dt)

        t_boids_update = pygame.time.get_ticks()

        self.wrap_boids()

        t_boids_wrap = pygame.time.get_ticks()

        self.game_state.state["t_sim_update_grid_rebuild"] = (
            f"{t_grid_rebuild - t_start} ms"
        )
        self.game_state.state["t_sim_update_neighbors_listing"] = (
            f"{t_sim_update_neighbors_listing - t_grid_rebuild} ms"
        )
        self.game_state.state["t_sim_update_boids_compute"] = (
            f"{t_boids_compute - t_sim_update_neighbors_listing} ms"
        )
        self.game_state.state["t_sim_update_boids_update"] = (
            f"{t_boids_update - t_boids_compute} ms"
        )
        self.game_state.state["t_sim_update_boids_wrap"] = (
            f"{t_boids_wrap - t_boids_update} ms"
        )

    def wrap_boids(self):

        for boid in self.boids:
            boid.position.x %= self.width
            boid.position.y %= self.height
