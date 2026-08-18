"""Simulation class"""

from random import randint

from .boid import Boid

class Simulation():

    def __init__(self, width, height, boids_count):
        self.width = width
        self.height = height

        self.boids = [
            Boid(randint(0, width - 1), randint(0, height - 1))
            for _ in range(0, boids_count)
        ]

    def update(self, dt):
        for boid in self.boids:
            boid.update(dt)

        self.wrap_boids()

    def wrap_boids(self):

        for boid in self.boids:
            boid.position.x %= self.width
            boid.position.y %= self.height

