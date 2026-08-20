"""InputManager Class for pygame"""

import pygame
import json


class InputManager:
    """Stores events in attributes, as well as keys and mouse"""

    def __init__(self):
        print("Initialising Input Manager")
        self._pressed = set()
        self._released = set()
        self._mouse_pressed = set()
        self._mouse_released = set()

        self.clear()

    def clear(self):
        """Clear events list and keys"""
        self._pressed.clear()
        self._released.clear()
        self._mouse_pressed.clear()
        self._mouse_released.clear()

        self.quit = False
        self.resize = False

    def update(self):
        # Clearing events state
        self.clear()

        # Hndling events
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    self.quit = True
                case pygame.KEYDOWN:
                    self._pressed.add(event.key)
                case pygame.KEYUP:
                    self._released.add(event.key)
                case pygame.MOUSEBUTTONDOWN:
                    self._mouse_pressed.add(event.button)
                case pygame.MOUSEBUTTONUP:
                    self._mouse_released.add(event.button)
                case pygame.VIDEORESIZE:
                    self.resize = (event.w, event.h)

        # Reloading keys and mouse
        self.keys = pygame.key.get_pressed()
        self.mouse = pygame.mouse.get_pressed()
        self.mouse_position = pygame.mouse.get_pos()

    def held(self, key):
        return self.keys[key]

    def pressed(self, key):
        return key in self._pressed
