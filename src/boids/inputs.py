"""Simple InputManager Class for pygame"""

import pygame
import json

"""(control name, key, 'pressed'|'held', default value)"""
# TODO: move to json configuration file
CONTROLS = [
    ("sim_paused", "K_SPACE", "pressed", False),
    ("quit", "K_q", "pressed", False),
    ("show_state", "K_e", "pressed", False),
    ("show_debug", "K_r", "pressed", False),
    ("boids_show_sensor", "K_z", "held", False),
    ("camera_move_left", "K_a", "held", False),
    ("camera_move_up", "K_w", "held", False),
    ("camera_move_right", "K_d", "held", False),
    ("camera_move_down", "K_s", "held", False),
    ("camera_zoom_up", "K_UP", "held", False),
    ("camera_zoom_down", "K_DOWN", "held", False),
]


class InputManager:
    def __init__(self):
        self.keys = pygame.key.get_pressed()
        self._pressed = set()
        self.quit = False

    def update(self):

        self._pressed.clear()
        self.quit = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit = True

            if event.type == pygame.KEYDOWN:
                self._pressed.add(event.key)
                if event.key in [pygame.K_ESCAPE, pygame.K_q]:
                    self.quit = True

        self.keys = pygame.key.get_pressed()

    def held(self, key):
        return self.keys[key]

    def pressed(self, key):
        return key in self._pressed


class GameState:
    def __init__(self):
        self.inputs = InputManager()
        self.key_bindings, self.state = self.build_key_binding(CONTROLS)

    def __str__(self):
        lines = [f"{k} = {v}" for k, v in self.get_state().items()]
        return "\n".join(lines)

    def build_key_binding(self, ctrl_list):
        """Build the key_bindings and state dictionaries from ctrl_list
        ctrl_list must be formatted as:
        [(control name, key, "pressed"|"held", default value), ...]
        """
        print("Building key bindings...")
        key_bindings = {"held": {}, "pressed": {}}
        state = {}

        for c in ctrl_list:
            key_bindings[c[2]][c[0]] = getattr(pygame, c[1])
            state[c[0]] = c[3]

        print(f"Key Bindings: {json.dumps(key_bindings, indent=4)}")
        print(f"Start State: {json.dumps(state, indent=4)}")
        return key_bindings, state

    def handle_inputs(self):
        """
        pressed: toggles the setting
        held: sets the setting to True
        """
        for name, key in self.key_bindings["pressed"].items():
            if self.inputs.pressed(key):
                self.state[name] = not self.state[name]

        for name, key in self.key_bindings["held"].items():
            self.state[name] = self.inputs.held(key)

    def update(self):
        self.inputs.update()
        self.handle_inputs()
        self.quit = self.inputs.quit or self.state["quit"]
