import math
import random

from .vector2 import Vector2


class Boid:

    sensor_range = 60

    def __init__(
        self,
        x=0,
        y=0,
        color="#AA2FA4",
        outline="#19033D",
        speed=30,
        direction=None,
        acceleration=None,
    ):
        self.position = Vector2(x, y)

        if direction is None:
            angle = random.uniform(0, 2 * math.pi)
            direction = Vector2(math.cos(angle), math.sin(angle))
        if acceleration is None:
            acceleration = Vector2(0, 0)

        self.velocity = direction * speed
        self.acceleration = acceleration

        self.color = color
        self.outline = outline

    def update(self, dt):
        self.velocity += self.acceleration * dt
        self.position += self.velocity * dt

        self.acceleration *= 0
