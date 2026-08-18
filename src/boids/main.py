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


def main_tk():
    # Creates Window
    root = tk.Tk()
    root.title(WIN_TITLE)
    root.attributes("-type", "dialog")  # allows for floating window in i3

    # Creates canvas for drawing
    canvas = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg=CANVAS_BG)
    canvas.pack()

    # Create fps counter
    frame_times = []
    last_frame = time.perf_counter()
    fps_label = tk.Label(
        root,
        text="FPS: -- | Frame: -- ms",
        bg="#1F1F1F",
        fg="white"
    )
    fps_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    print("Generating boids")
    Boid.canvas = canvas
    Boid.canvas_width = CANVAS_WIDTH
    Boid.canvas_height = CANVAS_HEIGHT

    boids = [
        Boid(randint(0, CANVAS_WIDTH - 1), randint(0, CANVAS_HEIGHT - 1))
        for _ in range(0, 100)
    ]

    print("Drawing boids")
    for b in boids:
        b.draw()

    def update():

        # FPS COUNTER UPDATE
        nonlocal last_frame

        now = time.perf_counter()
        frame_time = now - last_frame
        last_frame = now
        frame_times.append(frame_time)

        # Keep only the last 30 frames
        if len(frame_times) > 30:
            frame_times.pop(0)
        average_frame_time = sum(frame_times) / len(frame_times)
        fps = 1 / average_frame_time
        fps_label.config(
            text=f"{fps:5.1f} fps | Frame: {average_frame_time * 1000:5.1f} ms"
        )

        # MAIN LOOP
        canvas.delete("all")

        for b in boids:
            b.update()
            b.draw()

        root.after(16, update)

    update()

    print("Starting loop")
    root.mainloop()


def main():

    pygame.init()

    simulation = Simulation(
        WORLD_WIDTH,
        WORLD_HEIGHT,
        BOID_COUNT
    )

    renderer = Renderer(
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        BACKGROUND
    )

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
