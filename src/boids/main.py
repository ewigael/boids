import tkinter as tk
from random import randint
import time

from .boid import Boid

WIN_TITLE = "Boids by Akasha"
CANVAS_WIDTH = 1000
CANVAS_HEIGHT = 1000
CANVAS_BG = "#111111"


def main():
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


if __name__ == "__main__":
    main()
