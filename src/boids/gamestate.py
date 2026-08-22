import pygame
import json

"""(control name, key, 'toggle'|'action'|'held', default value)
    toggle is persistent
    action is played once
    held is continues boolean assignement
"""
# TODO: move to json configuration file
BINDINGS = [
    ("sim_paused", "K_SPACE", "pressed", False),
    ("quit", "K_q", "held", False),
    ("show_state", "K_e", "pressed", False),
    ("show_debug_next", "K_r", "action", False),
    ("boids_focus_next", "K_f", "action", False),
    ("boids_clear_focus", "K_ESCAPE", "held", False),
    ("boids_show_sensor", "K_z", "held", False),
    ("camera_move_left", "K_a", "held", False),
    ("camera_move_up", "K_w", "held", False),
    ("camera_move_right", "K_d", "held", False),
    ("camera_move_down", "K_s", "held", False),
    ("camera_zoom_up", "K_UP", "held", False),
    ("camera_zoom_down", "K_DOWN", "held", False),
    ("save_state", "K_o", "pressed", False),
]


class GameState:
    """Interprets inputs and update internal game state to be read by simulation and renderer"""

    def __init__(self, quiet, load_save=None):
        if not quiet:
            print("Initialising Game State...")
        self.key_bindings, self.state = self.build_key_binding(BINDINGS, quiet)

        if load_save:
            if not quiet:
                print("> Loading from file")
            for k, v in load_save["state"].items():
                self.state[k] = v
        else:
            # Simulation
            self.state["boids_count"] = None

            # Renderer
            self.state["focus_on"] = None
            self.state["focus"] = None
            self.state["show_debug"] = "fps_cam_perf"

        # General
        self.state["quit"] = False
        self.state["quiet"] = quiet

    def build_key_binding(self, ctrl_list, quiet):
        """Build the key_bindings and state dictionaries from ctrl_list
        ctrl_list must be formatted as:
        [(control name, key, "pressed"|"held", default value), ...]
        """
        if not quiet:
            print("> Building Key Bindings")
        key_bindings = {"held": {}, "action": {}, "pressed": {}}
        state = {}

        for c in ctrl_list:
            key_bindings[c[2]][c[0]] = getattr(pygame, c[1])
            state[c[0]] = c[3]

        return key_bindings, state

    def update(self, inputs):
        """Update internal game state by handling inputs from InputManager"""

        # interpret events
        self.state["win_resize"] = inputs.resize
        self.state["camera_zoom_on_mouse"] = inputs.mouse_wheel
        self.state["mouse_pos"] = inputs.mouse_position

        # interpret bindings
        # Toggles
        for name, key in self.key_bindings["pressed"].items():
            if inputs.pressed(key):
                self.state[name] = not self.state[name]

        # Continuous
        for name, key in self.key_bindings["held"].items():
            self.state[name] = inputs.held(key)

        # Once
        for name, key in self.key_bindings["action"].items():
            self.state[name] = inputs.pressed(key)

        # As the quit order can come from an event or keybinding it's updated last
        self.state["quit"] = inputs.quit or self.state["quit"]

        # interpret mouse
        if inputs.mouse_pressed(1):
            self.state["focus_on"] = inputs.mouse_position
