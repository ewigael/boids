"""Simple InputManager Class for pygame"""

import pygame


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

    KEY_BINDINGS = {
        "pressed": {
            pygame.K_SPACE: "sim_paused",
            pygame.K_q: "quit",
            pygame.K_e: "show_state",
        },
        "held": {
            pygame.K_r: "boids_show_sensor",
            pygame.K_a: "camera_move_left",
            pygame.K_w: "camera_move_up",
            pygame.K_d: "camera_move_right",
            pygame.K_s: "camera_move_down",
            pygame.K_UP: "camera_zoom_up",
            pygame.K_DOWN: "camera_zoom_down",
        },
    }

    def __init__(self):

        self.inputs = InputManager()

        self.quit = False
        self.sim_paused = False
        self.boids_show_sensor = False
        self.show_state = False
        self.camera_move_left = False
        self.camera_move_up = False
        self.camera_move_right = False
        self.camera_move_down = False
        self.camera_zoom_up = False
        self.camera_zoom_down = False

    def __str__(self):
        lines = [f"{k} = {v}" for k, v in self.get_state().items()]
        return "\n".join(lines)

    def get_state(self):
        return {
            "quit": self.quit,
            "sim_paused": self.sim_paused,
            "boids_show_sensor": self.boids_show_sensor,
            "show_state": self.show_state,
            "camera_move_left": self.camera_move_left,
            "camera_move_up": self.camera_move_up,
            "camera_move_right": self.camera_move_right,
            "camera_move_down": self.camera_move_down,
            "camera_zoom_up": self.camera_zoom_up,
            "camera_zoom_down": self.camera_zoom_down,
        }

    def handle_inputs(self):
        """
        pressed: toggles the setting
        held: sets the setting to True
        """
        for key in self.KEY_BINDINGS["pressed"]:
            if self.inputs.pressed(key):
                setting_state = getattr(self, self.KEY_BINDINGS["pressed"][key])
                setattr(self, self.KEY_BINDINGS["pressed"][key], not setting_state)

        for key in self.KEY_BINDINGS["held"]:
            setattr(self, self.KEY_BINDINGS["held"][key], self.inputs.held(key))

    def update(self):
        self.inputs.update()
        self.handle_inputs()
        self.quit = self.inputs.quit or self.quit
