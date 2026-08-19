"""Simulation class"""

from random import randint

from .boid import Boid
from .behaviors import flock


class Simulation:

    def __init__(self, game_state, width, height, boids_count):
        self.game_state = game_state
        self.width = width
        self.height = height

        self.boids = [
            Boid(randint(0, width - 1), randint(0, height - 1))
            for _ in range(0, boids_count)
        ]
        self.game_state.state["boids_count"] = boids_count

    def get_neighbors(self, boid):
        neighbors = []

        for other in self.boids:
            if boid is other:
                continue
            elif (boid.position + other.position).length() < boid.sensor_range:
                neighbors.append(other)

        return neighbors

    def update(self, dt):

        if self.game_state.state["sim_paused"]:
            return

        for boid in self.boids:
            neighbors = self.get_neighbors(boid)

            force = flock(boid, neighbors)

            boid.apply_force(force)

        for boid in self.boids:
            boid.update(dt)

        self.wrap_boids()

    def wrap_boids(self):

        for boid in self.boids:
            boid.position.x %= self.width
            boid.position.y %= self.height
