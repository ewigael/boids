import tkinter as tk
from random import randint
import time
import pygame

from .boid import Boid
from .simulation import Simulation
from .renderer import Renderer
from .vector2 import Vector2
from .inputs import GameState

WIN_TITLE = "Boids by Akasha"

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

BACKGROUND = "#0C0C0E"

WORLD_WIDTH = 1920
WORLD_HEIGHT = 1080

BOID_COUNT = 200


def main():

    pygame.init()

    game_state = GameState()

    simulation = Simulation(game_state, WORLD_WIDTH, WORLD_HEIGHT, BOID_COUNT)
    renderer = Renderer(game_state, SCREEN_WIDTH, SCREEN_HEIGHT, simulation, BACKGROUND)
    clock = pygame.time.Clock()

    while not game_state.state["quit"]:

        dt = clock.tick(60) / 1000.0
        game_state.update()

        t_start = pygame.time.get_ticks()

        renderer.handle_inputs(dt)
        t_renderer_handle_inputs = pygame.time.get_ticks()

        simulation.update(dt)
        t_sim_update = pygame.time.get_ticks()

        renderer.draw(clock.get_fps())
        t_renderer_draw = pygame.time.get_ticks()

        game_state.state["t_renderer_handle_inputs"] = (
            f"{t_renderer_handle_inputs - t_start} ms"
        )
        game_state.state["t_sim_update"] = (
            f"{t_sim_update - t_renderer_handle_inputs} ms"
        )
        game_state.state["t_renderer_draw"] = f"{t_renderer_draw - t_sim_update} ms"

    pygame.quit()


if __name__ == "__main__":
    main()
