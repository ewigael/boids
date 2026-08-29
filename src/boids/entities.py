"""Entities management class"""

import numpy as np

from .colors import small_change_hex


class Entities:

    initial_speed = 100

    min_speed = 70
    max_speed = 150

    sensor_range = 60
    sensor_range_squared = sensor_range**2

    def __init__(self, gamestate, count=0, width=0, height=0, load_save=None):

        # self.species_color = "#F0C580"  # gold
        # self.species_color = "#FF00EE"  # super pink
        self.species_color = "#F080E9"  # pink
        self.gamestate = gamestate

        if not gamestate["quiet"]:
            print(f"> Generating entities ({count})")

        if load_save:
            self.load_from_save(load_save)
            return

        self.width = width
        self.height = height

        self.count = count
        self.gamestate["boids_count"] = count

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
        self.speeds = np.linalg.norm(self.velocities, axis=1)
        self.accelerations = np.zeros((count, 2), dtype=np.float32)
        self.colors = [small_change_hex(self.species_color) for _ in range(0, count)]

    def update_all(self, dt):
        """Update all entities, taking advantage of numpy"""

        # Applying accelerations
        self.velocities += self.accelerations * dt
        self.accelerations.fill(0)

        # Clamping speeds
        speed_squared = np.sum(self.velocities**2, axis=1)

        too_slow = speed_squared < self.min_speed**2
        too_fast = speed_squared > self.max_speed**2

        # TODO: Remove unnecessary square roots
        speeds = np.sqrt(speed_squared)

        self.velocities[too_slow] *= self.min_speed / speeds[too_slow, None]
        self.velocities[too_fast] *= self.max_speed / speeds[too_fast, None]

        # Updating positions
        self.positions += self.velocities * dt
        self.speeds = np.linalg.norm(self.velocities, axis=1)

    def add(self, n):
        for _ in range(0, n):
            self.positions = np.vstack(
                [
                    self.positions,
                    np.random.randint(0, [self.width, self.height], size=(1, 2)).astype(
                        np.float32
                    ),
                ]
            )
            self.velocities = np.vstack(
                [
                    self.velocities,
                    np.random.randint(0, [self.width, self.height], size=(1, 2)).astype(
                        np.float32
                    ),
                ]
            )
            self.accelerations = np.vstack([self.accelerations, np.zeros(2)])
            self.colors.append(small_change_hex(self.species_color))

            self.count += 1
        self.gamestate["boids_count"] = self.count

    def remove(self, n):
        for _ in range(0, n):
            self.positions = np.delete(self.positions, -1, axis=0)
            self.velocities = np.delete(self.velocities, -1, axis=0)
            self.accelerations = np.delete(self.accelerations, -1, axis=0)
            self.colors.pop()

            self.count -= 1
        self.gamestate["boids_count"] = self.count

    def to_list(self):
        """Returns a list version of Entities data, to be used for serialization"""
        return {
            "count": self.count,
            "positions": self.positions.tolist(),
            "velocities": self.velocities.tolist(),
            "speeds": self.speeds.tolist(),
            "accelerations": self.accelerations.tolist(),
            "colors": self.colors,
        }

    def load_from_save(self, load_save):
        self.width = load_save["world"]["width"]
        self.height = load_save["world"]["height"]
        self.count = load_save["entities"]["count"]
        self.positions = np.array(load_save["entities"]["positions"], dtype=np.float32)
        self.velocities = np.array(
            load_save["entities"]["velocities"], dtype=np.float32
        )
        self.speeds = np.array(load_save["entities"]["speeds"], dtype=np.float32)
        self.accelerations = np.array(
            load_save["entities"]["accelerations"], dtype=np.float32
        )
        self.colors = load_save["entities"]["colors"]
