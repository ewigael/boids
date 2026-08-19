"""Simple InputManager Class for pygame"""

import pygame


class InputManager:
    def __init__(self):
        self.quit = False

    def update(self):
        self.quit = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit = True

            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE, pygame.K_q]:
                    self.quit = True

        self.keys = pygame.key.get_pressed()

    def pressed(self, key):
        return self.keys[key]
