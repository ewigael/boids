import tkinter as tk
from random import randint
import time
import pygame

from .boid import Boid
from .simulation import Simulation
from .renderer import Renderer
from .vector2 import Vector2

WIN_TITLE = "Boids by Akasha"

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

BACKGROUND = "#0C0C0E"

WORLD_WIDTH = 1920
WORLD_HEIGHT = 1080

BOID_COUNT = 200


def main():

    pygame.init()

    simulation = Simulation(WORLD_WIDTH, WORLD_HEIGHT, BOID_COUNT)
    renderer = Renderer(SCREEN_WIDTH, SCREEN_HEIGHT, simulation, BACKGROUND)
    camera = renderer.camera
    clock = pygame.time.Clock()

    running = True

    while running:

        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE, pygame.K_q]:
                    running = False

        if not running:
            break

        keys = pygame.key.get_pressed()
        movement = Vector2(0, 0)

        if keys[pygame.K_a]:
            movement.x -= 1
        if keys[pygame.K_d]:
            movement.x += 1
        if keys[pygame.K_w]:
            movement.y -= 1
        if keys[pygame.K_s]:
            movement.y += 1
        camera_movement = movement.length()
        if camera_movement > 0:
            if camera_movement > 1:
                camera.move(movement.normalize() * camera.speed * dt)
            else:
                camera.move(movement * camera.speed * dt)

        if keys[pygame.K_UP]:
            camera.zoom_by(1 - 2 * dt)

        if keys[pygame.K_DOWN]:
            camera.zoom_by(1 + 2 * dt)

        simulation.update(dt)
        renderer.draw(clock.get_fps())

    pygame.quit()


if __name__ == "__main__":
    main()
