import math
import random

from .vector2 import Vector2

class Boid:

    canvas = None
    canvas_width = 0
    canvas_height = 0

    def __init__(
        self,
        x=0,
        y=0,
        color="#AA2FA4",
        outline="#19033D",
        speed=7,
        direction=None,
        acceleration=None,
    ):
        self.position = Vector2(x, y)

        if direction is None:
            angle = random.uniform(0, 2 * math.pi)
            direction = Vector2(
                math.cos(angle),
                math.sin(angle)
            )
        if acceleration is None:
            acceleration = Vector2(0, 0)

        self.velocity = direction * speed
        self.acceleration = acceleration

        self.color = color
        self.outline = outline

    def draw(self):
        direction = self.velocity.normalize()
        perpendicular = Vector2(-direction.y, direction.x)

        tip = self.position + direction * 12
        back = self.position - direction * 8
        left = back + perpendicular * 6
        right = back - perpendicular * 6

        self.canvas.create_polygon(
            tip.x, tip.y,
            left.x, left.y,
            right.x, right.y,
            fill=self.color,
            outline=self.outline
        )
    
    def wrap(self):
        width = self.canvas_width
        height = self.canvas_height


        self.position.x %= width
        self.position.y %= height
    
    def update(self):
        self.velocity += self.acceleration
        self.position += self.velocity
        self.wrap()

        self.acceleration *= 0
