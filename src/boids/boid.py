import math
import random

from .vector2 import Vector2
from .colors import small_change_hex


class Boid:

    sensor_range = 60
    min_speed = 60
    max_speed = 200
    sensor_range_squared = 60**2

    def __init__(
        self,
        x=0,
        y=0,
        color="#AA2FA4",
        speed=100,
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

    def is_in_range(self, other):
        """Tells if another boid is in range of this one.
        this is used to avoid repeated square root computations when doing
        (boid.position - other.position).length() < boid.sensor_range

        Should be ran against candidates provided by a spatial grid"""

        spos = self.position
        opos = other.position

        return (spos.x - opos.x) ** 2 + (
            spos.y - opos.y
        ) ** 2 < self.sensor_range_squared

    def apply_force(self, force):
        self.acceleration += force

    def update(self, dt):

        # Applying acceleration
        self.velocity.x += self.acceleration.x * dt
        self.velocity.y += self.acceleration.y * dt

        # Speed clamping
        speed_squared = self.velocity.x**2 + self.velocity.y**2
        if speed_squared < self.min_speed**2 or speed_squared > self.max_speed**2:
            speed = self.velocity.length()
            if speed != 0:
                factor = (
                    self.min_speed if speed < self.min_speed else self.max_speed
                ) / speed
                self.velocity *= factor

        # Updating position
        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt

        self.acceleration *= 0
