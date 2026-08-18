import pygame

from .vector2 import Vector2

class Camera():
    def __init__(self, position, zoom=1.0):
        """position refers to the simulation's world coordinates"""
        self.postion = position
        self.zoom = zoom

    def world_to_screen(self, world_position, screen_w, screen_h):
        relative = world_position - self.postion
        return Vector2(
            relative.x - self.zoom + screen_w / 2,
            relative.y - self.zoom + screen_h / 2,
        )

class Renderer():
    def __init__(self, width, height, background="#0C0C0E"):
        
        self.width = width
        self.height = height
        self.background = background

        self.screen = pygame.display.set_mode(
            (width, height)
        )

        self.camera = Camera(
            position=Vector2(
                self.width / 2,
                self.height / 2
            )
        )
    
    def draw(self, simulation):
        self.screen.fill(self.background)

        for boid in simulation.boids:
            position = self.camera.world_to_screen(boid.position, self.width, self.height)

            pygame.draw.circle(
                self.screen,
                "#AA2FA4",
                (int(position.x), int(position.y)),
                4
            )

        pygame.display.flip()