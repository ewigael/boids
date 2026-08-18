import tkinter as tk
from random import randint
import time
import pygame

from .boid import Boid
from .simulation import Simulation
from .renderer import Renderer

WIN_TITLE = "Boids by Akasha"

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

BACKGROUND = "#0C0C0E"

WORLD_WIDTH = 1920
WORLD_HEIGHT = 1080

BOID_COUNT = 100


def main():

    pygame.init()

    simulation = Simulation(WORLD_WIDTH, WORLD_HEIGHT, BOID_COUNT)

    renderer = Renderer(SCREEN_WIDTH, SCREEN_HEIGHT, BACKGROUND)

    clock = pygame.time.Clock()

    running = True

    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        dt = clock.tick(60) / 1000.0

        simulation.update(dt)
        renderer.draw(simulation)

    pygame.quit()


if __name__ == "__main__":
    main()
