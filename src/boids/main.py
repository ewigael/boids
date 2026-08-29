import os
import json

# Quiets pygame prompt
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import click
import pygame
from pathlib import Path
from perflogger import PerfLogger

from . import print_metadata
from .config import config as conf
from .inputs import InputManager
from .gamestate import GameState
from .simulation import Simulation
from .renderer import Renderer

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
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Load a user conf file (see boids/default_conf.toml for syntax)",
)
@click.option("-r", "--record-data-to-file", type=click.Path(), default=None)
def main(quiet, load_save, config, record_data_to_file):
    if not quiet:
        print_metadata(pygame)

    if record_data_to_file is not None:
        data_output_path = Path(record_data_to_file)
    else:
        data_output_path = None

    user_config = Path(os.path.expandvars(conf.general.config)).expanduser()
    if user_config.exists():
        if not quiet:
            print(f"Overlaying config from: {user_config}")
        conf.overlay(user_config)

    if config:
        if not quiet:
            print(f"Overlaying config from: {config}")
        conf.overlay(config)

    if load_save:
        if not quiet:
            print(f"Loading save file: {load_save}")
        with open(load_save, "r") as save_file:
            load_save = json.load(save_file)

    pygame.init()

    perflog = PerfLogger("main", output_file_path=data_output_path)

    gamestate = GameState(quiet, load_save)
    gamestate.state["data_output_path"] = data_output_path
    inputs = InputManager(gamestate)

    simulation = Simulation(gamestate, BOID_COUNT, load_save=load_save)
    renderer = Renderer(
        gamestate,
        simulation,
    )

    clock = pygame.time.Clock()

    while not gamestate.state["quit"]:

        dt = clock.tick(60) / 1000.0

        perflog.start()

        inputs.update()
        perflog.add("inputs update")
        gamestate.update(inputs)
        perflog.add("game state update")

        simulation.update_entities(dt)
        perflog.add("simulation update entities")

        renderer.handle_inputs(dt)
        perflog.add("renderer handle inputs")

        renderer.draw(clock.get_fps())
        perflog.add("renderer draw")

    pygame.quit()


if __name__ == "__main__":
    main()
