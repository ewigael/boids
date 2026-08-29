import pygame
import numpy as np
from pathlib import Path
import json
import os

from perflogger import PerfLogger

from .config import config

from .vector2 import Vector2
from .colors import value_to_color_gradient_linear, value_to_color_gradient_log

DEBUG_CYCLE = [None, "fps", "fps_cam", "fps_cam_perf"]


class Camera:
    def __init__(
        self,
        position=None,
        speed=1000,
        zoom=None,
    ):
        """position refers to the simulation's world coordinates"""
        self.speed = speed

        if position:
            self.position = position
        else:
            self.position = Vector2(0, 0)
            self.center_on_world()

        self.min_zoom = self.get_min_zoom()
        if zoom:
            self.zoom = zoom
        else:
            self.zoom = self.min_zoom

    def clamp_position(self):
        """Forces the camera's position to adapt to screen size for zooming out"""
        half_width = config.display.width / (2 * self.zoom)
        half_height = config.display.height / (2 * self.zoom)

        min_x = half_width
        max_x = config.world.width - half_width

        min_y = half_height
        max_y = config.world.height - half_height

        self.position.x = max(min_x, min(self.position.x, max_x))
        self.position.y = max(min_y, min(self.position.y, max_y))

    def get_min_zoom(self):
        return max(
            config.display.width / config.world.width,
            config.display.height / config.world.height,
        )

    def set_screen_size(self, new_w, new_h):
        config.display.width = new_w
        config.display.height = new_h

        self.min_zoom = self.get_min_zoom()
        self.set_zoom(self.zoom)

    def move(self, movement):
        self.position += movement
        self.clamp_position()

    def set_zoom(self, zoom):
        self.zoom = max(self.min_zoom, zoom)
        self.clamp_position()

    def zoom_by(self, factor):
        self.set_zoom(self.zoom * factor)

    def zoom_at(self, target, factor):
        before = self.screen_to_world(target)
        self.zoom_by(factor)
        after = self.screen_to_world(target)

        self.position += before - after
        self.clamp_position()

    def focus_on(self, x, y):
        self.position.x = x
        self.position.y = y
        self.clamp_position()

    def center_on_world(self):
        self.position.x = config.world.width / 2
        self.position.y = config.world.height / 2

    def world_to_screen(self, world_position):
        relative = world_position - self.position

        return Vector2(
            relative.x * self.zoom + config.display.width / 2,
            relative.y * self.zoom + config.display.height / 2,
        )

    def screen_to_world(self, screen_position):
        if type(screen_position) == Vector2:
            spos_x, spos_y = screen_position.x, screen_position.y
        elif type(screen_position) == tuple:
            spos_x, spos_y = screen_position

        return Vector2(
            (spos_x - config.display.width / 2) / self.zoom + self.position.x,
            (spos_y - config.display.height / 2) / self.zoom + self.position.y,
        )

    def world_to_screen_tuple(self, world_position):
        relative = (
            world_position[0] - self.position.x,
            world_position[1] - self.position.y,
        )

        return (
            relative[0] * self.zoom + config.display.width / 2,
            relative[1] * self.zoom + config.display.height / 2,
        )

    def screen_to_world_tuple(self, screen_position):
        spos_x, spos_y = screen_position
        cpos_x, cpos_y = self.position.astuple()

        return (
            (spos_x - config.display.width / 2) / self.zoom + cpos_x,
            (spos_y - config.display.height / 2) / self.zoom + cpos_y,
        )

    @property
    def world_bounds(self):
        posx, posy = self.position.astuple()
        w_width = config.display.width / (2 * self.zoom)
        w_height = config.display.height / (2 * self.zoom)

        return (
            posx - w_width,  # left
            posx + w_width,  # right
            posy - w_height,  # top
            posy + w_height,  # bottom
        )


class Renderer:
    def __init__(
        self,
        gamestate,
        simulation,
    ):
        if not gamestate.state["quiet"]:
            print("Initialising Renderer...")
        self.gamestate = gamestate.state

        self.simulation = simulation

        self.screen = pygame.display.set_mode(
            (config.display.width, config.display.height), pygame.RESIZABLE
        )
        pygame.display.set_caption(config.display.title)

        self.font = pygame.font.SysFont(
            ["JetBrains Mono Nerd Font", "JetBrains Mono", "monospace"],
            16,
        )

        self.camera = Camera()

        self.pl_draw = PerfLogger("Renderer-Draw")

    def draw_vector(self, origin, vector, color):
        """Draw a given vector as a color colored arrow with origin as origin"""

        vx, vy = vector
        length = (vx * vx + vy * vy) ** 0.5

        if length == 0:
            return

        ox, oy = origin

        dir_x = vx / length
        dir_y = vy / length

        end_x = ox + vx
        end_y = oy + vy

        perp_x = -dir_y
        perp_y = dir_x

        head_length = 6
        head_width = 2

        left_x = end_x - dir_x * head_length + perp_x * head_width
        left_y = end_y - dir_y * head_length + perp_y * head_width
        right_x = end_x - dir_x * head_length - perp_x * head_width
        right_y = end_y - dir_y * head_length - perp_y * head_width

        start_screen = self.camera.world_to_screen_tuple(origin)
        end_screen = self.camera.world_to_screen_tuple((end_x, end_y))
        left_screen = self.camera.world_to_screen_tuple((left_x, left_y))
        right_screen = self.camera.world_to_screen_tuple((right_x, right_y))

        pygame.draw.aaline(
            self.screen,
            color,
            (int(start_screen[0]), int(start_screen[1])),
            (int(end_screen[0]), int(end_screen[1])),
            2,
        )

        pygame.draw.polygon(
            self.screen,
            color,
            [
                (int(end_screen[0]), int(end_screen[1])),
                (int(left_screen[0]), int(left_screen[1])),
                (int(right_screen[0]), int(right_screen[1])),
            ],
        )

    def draw_debug(self, camera, fps):

        debug_mode = self.gamestate["show_debug"]
        margin = 10
        line_height = self.font.get_height() + 3
        lines = []

        if "fps" in debug_mode:
            lines.append((f"FPS: {fps:.1f}", "white"))

        if "cam" in debug_mode:
            lines.append(
                (f"Camera: ({camera.position.x:.1f}, {camera.position.y:.1f})", "white")
            )
            lines.append((f"Zoom: {camera.zoom:.2f}x", "white"))

        if "perf" in debug_mode:
            for logger in PerfLogger.get_all_instances():
                lines.append((f"Performance Logger #{logger.name}", "#F5F5F5"))

                for name, delta, true in logger.get_averages():
                    color = value_to_color_gradient_log(
                        true,
                        0.05 * 1e-6,
                        10 * 1e-3,
                    )

                    lines.append((f"{name} {delta:>9s}", color))

        for i, (line, color) in enumerate(lines):
            text = self.font.render(line, True, color)
            x = config.display.width - text.get_width() - margin
            y = config.display.height - (len(lines) - i) * line_height - margin
            self.screen.blit(text, (x, y))

    def draw_state(self):

        hidden_values = ["quit", "show_state"]

        margin = 10
        line_height = self.font.get_height() + 3
        full_height = len(self.gamestate) - len(hidden_values)

        i = 0
        for line, value in self.gamestate.items():
            if line in hidden_values:
                continue

            if type(value) == bool:
                text = self.font.render(line, True, "#A1D319" if value else "#DB3A3A")
            elif value is None:
                text = self.font.render(f"{line} = None", True, "#717171")
            else:
                text = self.font.render(f"{line} = {value}", True, "#C4C4C4")

            x = margin
            y = config.display.height - (full_height - i) * line_height - margin

            self.screen.blit(text, (x, y))
            i += 1

    def draw_focused_data(self, bid):
        entities = self.simulation.entities
        velocity = entities.velocities[bid]
        speed = (velocity[0] ** 2 + velocity[1] ** 2) ** 0.5
        lines = [
            f"Boid #{bid}",
            "",
            f"Position X {entities.positions[bid][0]:8.2f}",
            f"Y {entities.positions[bid][1]:8.2f}",
            f"Velocity X {velocity[0]:8.2f}",
            f"Y {velocity[1]:8.2f}",
            f"Speed {speed:8.2f}",
            "",
            f"Neighbors: {len(self.simulation.get_neighbors(bid))}",
            "",
            "",
            f"Speed range: {entities.min_speed} {entities.max_speed}",
            f"Color: {entities.colors[bid]}",
            "",
            f"ESC to unfocus",
        ]

        margin = 10
        line_height = self.font.get_height() + 3

        for i, line in enumerate(lines):
            text = self.font.render(
                line,
                True,
                "#E5D68B",
            )

            x = config.display.width - text.get_width() - margin
            y = i * line_height + margin

            self.screen.blit(text, (x, y))

    def draw_entities(self):
        """Perform a culling before drawing entities"""
        cull_margin = 25

        left, right, top, bottom = self.camera.world_bounds
        positions = self.simulation.entities.positions
        eligible_mask = (
            (positions[:, 0] >= left - cull_margin)
            & (positions[:, 0] <= right + cull_margin)
            & (positions[:, 1] >= top - cull_margin)
            & (positions[:, 1] <= bottom + cull_margin)
        )

        eligible_ids = np.flatnonzero(eligible_mask)
        for bid in eligible_ids:
            self.draw_entity(bid)

    def draw_entity(self, bid):

        entities = self.simulation.entities
        focused = self.gamestate["focus"] == bid

        position = entities.positions[bid]
        screen_pos_x, screen_pos_y = self.camera.world_to_screen_tuple(position)
        velocity = entities.velocities[bid]

        speed = entities.speeds[bid]
        direction = velocity / speed

        if focused and self.simulation.neighbors_ready:

            # Sensor circle
            s_range = self.simulation.entities.sensor_range * self.camera.zoom
            pygame.draw.aacircle(
                self.screen,
                "#D3C6B2",
                (int(screen_pos_x), int(screen_pos_y)),
                s_range,
                2,
            )

            # Candidates lines
            candidates = self.simulation.get_candidates(bid)
            for nib in candidates:
                nx, ny = self.camera.world_to_screen_tuple(entities.positions[nib])
                pygame.draw.aaline(
                    self.screen,
                    "#404040",
                    (int(screen_pos_x), int(screen_pos_y)),
                    (int(nx), int(ny)),
                    2,
                )

            # Neighbor lines
            neighbors = self.simulation.get_neighbors(bid)
            for nib in neighbors:
                nx, ny = self.camera.world_to_screen_tuple(entities.positions[nib])
                pygame.draw.aaline(
                    self.screen,
                    "#CBCBCB",
                    (int(screen_pos_x), int(screen_pos_y)),
                    (int(nx), int(ny)),
                    2,
                )

            # Direction vector
            self.draw_vector(position, velocity, "#FFDE4B")

        # Draw boid body
        tip = position + direction * 12
        back = position - direction * 8

        perp_x = -direction[1]
        perp_y = direction[0]

        left = (back[0] + perp_x * 6, back[1] + perp_y * 6)
        right = (back[0] - perp_x * 6, back[1] - perp_y * 6)

        tip = self.camera.world_to_screen_tuple(tip)
        left = self.camera.world_to_screen_tuple(left)
        right = self.camera.world_to_screen_tuple(right)

        body_points = [
            (int(tip[0]), int(tip[1])),
            (int(left[0]), int(left[1])),
            (int(screen_pos_x), int(screen_pos_y)),
            (int(right[0]), int(right[1])),
        ]

        pygame.draw.polygon(
            self.screen, "#CC2424" if focused else entities.colors[bid], body_points
        )

    def handle_inputs(self, dt):

        # CAMERA ####
        # Repositionning
        movement = Vector2(0, 0)
        if self.gamestate["camera_move_left"]:
            movement.x -= 1
        if self.gamestate["camera_move_right"]:
            movement.x += 1
        if self.gamestate["camera_move_up"]:
            movement.y -= 1
        if self.gamestate["camera_move_down"]:
            movement.y += 1

        camera_movement = movement.length()
        if camera_movement > 0:
            if camera_movement > 1:
                self.camera.move(movement.normalize() * self.camera.speed * dt)
            else:
                self.camera.move(movement * self.camera.speed * dt)

        # Zooming
        if self.gamestate["camera_zoom_up"]:
            self.camera.zoom_by(1 + 2 * dt)
        if self.gamestate["camera_zoom_down"]:
            self.camera.zoom_by(1 - 2 * dt)

        # Zooming on mouse
        if self.gamestate["camera_zoom_on_mouse"]:
            self.camera.zoom_at(
                self.gamestate["mouse_pos"],
                1 + 3 * dt * self.gamestate["camera_zoom_on_mouse"],
            )

        # FOCUS ####
        # Focusing
        if self.gamestate["boids_focus_next"]:
            cur_foc = self.gamestate["focus"]
            self.gamestate["focus"] = (
                ((cur_foc + 1) % self.simulation.entities.count)
                if cur_foc is not None
                else 0 if self.simulation.entities.count else None
            )
            self.camera.set_zoom(3)

        # Boid control
        if self.gamestate["focus"] is not None and (
            self.gamestate["focus_boid_go_left"]
            or self.gamestate["focus_boid_go_right"]
        ):
            focused = self.gamestate["focus"]
            vel = self.simulation.entities.velocities[focused]
            if self.simulation.entities.speeds[focused] > 0:
                perp = (
                    np.array([vel[1], -vel[0]])
                    / self.simulation.entities.speeds[focused]
                )
            else:
                perp = np.zeros(2)
            if self.gamestate["focus_boid_go_left"]:
                self.gamestate["focus_boid_go_direction"] = (
                    perp * self.simulation.entities.speeds[focused]
                )
            if self.gamestate["focus_boid_go_right"]:
                self.gamestate["focus_boid_go_direction"] = (
                    -perp * self.simulation.entities.speeds[focused]
                )
        else:
            self.gamestate["focus_boid_go_direction"] = None

        # Clearing focus
        if self.gamestate["boids_clear_focus"]:
            self.gamestate["focus"] = None

        # WINDOW ####
        # Resizing
        if self.gamestate["win_resize"]:
            new_w, new_h = self.gamestate["win_resize"]
            config.display.width = new_w
            config.display.height = new_h
            self.camera.set_screen_size(new_w, new_h)
            self.gamestate["win_resize"] = None

        # DEBUG ####
        # cycle show_debug
        if self.gamestate["show_debug_next"]:
            self.gamestate["show_debug"] = DEBUG_CYCLE[
                (DEBUG_CYCLE.index(self.gamestate["show_debug"]) + 1) % len(DEBUG_CYCLE)
            ]

        # SAVE STATE ####
        if self.gamestate["save_state"]:
            self.gamestate["save_state"] = None
            self.save_state()

        # SPAWN ######
        # TODO: move this to be handled by the simulation?
        if self.gamestate["boids_add"]:
            self.simulation.entities.add(1)
        if self.gamestate["boids_rem"]:
            self.simulation.entities.remove(1)

    def draw(self, fps):
        """Read game state to know what and how to draw it"""

        self.pl_draw.start()

        self.screen.fill(config.display.background)
        self.pl_draw.add("fill")

        if self.gamestate["focus_on"]:
            self.gamestate["focus"] = self.simulation.find_boid_at(
                self.camera.screen_to_world_tuple(self.gamestate["focus_on"])
            )
            self.gamestate["focus_on"] = None

        if self.gamestate["focus"] is not None:
            self.camera.focus_on(
                *self.simulation.entities.positions[self.gamestate["focus"]]
            )

        self.pl_draw.add("focusing")

        self.draw_entities()

        self.pl_draw.add("drawing boids")

        if self.gamestate["focus"] is not None:
            self.draw_focused_data(self.gamestate["focus"])

        self.pl_draw.add("focus data")

        if self.gamestate["show_debug"]:
            self.draw_debug(self.camera, fps)

        self.pl_draw.add("show debug")

        if self.gamestate["show_state"]:
            self.draw_state()

        self.pl_draw.add("show state")

        pygame.display.flip()

    def save_state(
        self, dest=Path(os.path.expandvars(config.general.saves)), force_write=False
    ):
        or_stem = dest.stem
        dest = dest.expanduser()
        dest.parent.mkdir(parents=True, exist_ok=True)

        i = 1
        while not force_write and dest.exists():
            file_name = f"{or_stem}{i}{dest.suffix}"
            dest = dest.parent / file_name
            i += 1

        state = {
            "state": {
                k: (
                    v.to_list()
                    if k == "focus_boid_go_direction" and v is not None
                    else v
                )
                for k, v in self.gamestate.items()
            },
            "world": (config.world.width, config.world.height),
            "entities": self.simulation.entities.to_list(),
        }

        with open(dest, "w") as file:
            json.dump(state, file, indent=4)

        if not self.gamestate["quiet"]:
            print(f"Saved at {dest}")
