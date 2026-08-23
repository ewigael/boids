import os
import json

# Quiets pygame prompt
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import click
import pygame
from pathlib import Path
from perflogger import PerfLogger

from . import print_metadata
from .inputs import InputManager
from .gamestate import GameState
from .simulation import Simulation
from .renderer import Renderer

WIN_TITLE = "Boids by Akasha"

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

BACKGROUND = "#0C0C0E"

WORLD_WIDTH = 1920
WORLD_HEIGHT = 1080

BOID_COUNT = 200


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    show_default=True,
    default=False,
    help="Quiet the console output",
)
@click.option(
    "-l",
    "--load-save",
    type=click.Path(exists=True, path_type=Path),
    help="Load a .boids save file, loads game state and simulation state",
)
def main(quiet, load_save):
    if not quiet:
        print_metadata(pygame)

    perflog = PerfLogger("main")

    if load_save:
        if not quiet:
            print(f"Loading save file: {load_save}")
        with open(load_save, "r") as save_file:
            load_save = json.load(save_file)

    pygame.init()

    gamestate = GameState(quiet, load_save)
    inputs = InputManager(gamestate)

    simulation = Simulation(
        gamestate, WORLD_WIDTH, WORLD_HEIGHT, BOID_COUNT, load_save=load_save
    )
    renderer = Renderer(
        gamestate, simulation, SCREEN_WIDTH, SCREEN_HEIGHT, WIN_TITLE, BACKGROUND
    )

    clock = pygame.time.Clock()

    while not gamestate.state["quit"]:

        dt = clock.tick(60) / 1000.0

        perflog.start()
        inputs.update()
        perflog.add("inputs update")
        gamestate.update(inputs)
        perflog.add("game state update")

        simulation.update(dt)
        perflog.add("simulation update")

        renderer.handle_inputs(dt)
        perflog.add("renderer handle inputs")

        renderer.draw(clock.get_fps())
        perflog.add("renderer draw")

    pygame.quit()


if __name__ == "__main__":
    main()
