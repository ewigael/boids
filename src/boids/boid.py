import math
import random

from .vector2 import Vector2
from .colors import small_change_hex


class Boid:

    sensor_range = 600

    def __init__(
        self,
        x=0,
        y=0,
        color="#AA2FA4",
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

        self.color = small_change_hex(color)

    def apply_force(self, force):
        self.acceleration += force

    def update(self, dt):
        self.velocity += self.acceleration * dt
        self.position += self.velocity * dt

        self.acceleration *= 0
