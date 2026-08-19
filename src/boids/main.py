import tkinter as tk
from random import randint
import time
import pygame

from .boid import Boid
from .simulation import Simulation
from .renderer import Renderer
from .vector2 import Vector2
from .inputs import InputManager

WIN_TITLE = "Boids by Akasha"

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

BACKGROUND = "#0C0C0E"

WORLD_WIDTH = 1920
WORLD_HEIGHT = 1080

BOID_COUNT = 1000


def main():

    pygame.init()

    simulation = Simulation(WORLD_WIDTH, WORLD_HEIGHT, BOID_COUNT)
    renderer = Renderer(SCREEN_WIDTH, SCREEN_HEIGHT, simulation, BACKGROUND)
    camera = renderer.camera
    clock = pygame.time.Clock()

    inputs = InputManager()

    while not inputs.quit:

        dt = clock.tick(60) / 1000.0
        inputs.update()

        camera.handle_inputs(inputs, dt)

        simulation.update(dt)

        renderer.draw(clock.get_fps())

    pygame.quit()


if __name__ == "__main__":
    main()
