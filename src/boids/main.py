import tkinter as tk
from random import randint

from .boid import Boid

WIN_TITLE = "Boids by Akasha"
CANVAS_WIDTH = 1000
CANVAS_HEIGHT = 1000
CANVAS_BG = "#1F1F1F"


def main():
    # Creates Window
    root = tk.Tk()
    root.title = WIN_TITLE
    root.attributes("-type", "dialog")  # allows for floating window in i3

    # Creates canvas for drawing
    canvas = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg=CANVAS_BG)
    canvas.pack()

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
        canvas.delete("all")
        for b in boids:
            b.update()
            b.draw()
        root.after(16, update)
    
    print("Starting update loop")
    update()

    root.mainloop()


if __name__ == "__main__":
    main()
