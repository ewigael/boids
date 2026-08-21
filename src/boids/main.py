import pygame

from . import print_metadata
from .inputs import InputManager
from .gamestate import GameState
from .simulation import Simulation
from .renderer import Renderer
from .perflog import PerformanceLogger

WIN_TITLE = "Boids by Akasha"

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

BACKGROUND = "#0C0C0E"

WORLD_WIDTH = 1920
WORLD_HEIGHT = 1080

BOID_COUNT = 200


def main():
    print_metadata()

    perflog = PerformanceLogger("main")

    pygame.init()

    inputs = InputManager()
    gamestate = GameState()

    simulation = Simulation(gamestate, WORLD_WIDTH, WORLD_HEIGHT, BOID_COUNT)
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
