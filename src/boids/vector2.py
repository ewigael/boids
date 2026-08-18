from math import sqrt


class Vector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def dotnorm(self, other):
        return self.normalize().dot(other.normalize())

    def length(self):
        return sqrt(self.x**2 + self.y**2)

    def normalize(self):
        length = self.length()
        return Vector2(self.x / length, self.y / length)
