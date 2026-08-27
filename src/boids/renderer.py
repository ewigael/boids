import pygame
from pathlib import Path
import json
import numpy as np

from .vector2 import Vector2
from perflogger import PerfLogger
from .colors import value_to_color_gradient_linear, value_to_color_gradient_log
from .boid import Boid
from random import randint

SAVE_STATE_FILE = Path("./saves/save.boids")
DEBUG_CYCLE = [None, "fps", "fps_cam", "fps_cam_perf"]


class Camera:
    def __init__(
        self,
        world_width,
        world_height,
        screen_width,
        screen_height,
        position=None,
        speed=1000,
        zoom=None,
    ):
        """position refers to the simulation's world coordinates"""
        self.speed = speed

        self.world_width = world_width
        self.world_height = world_height
        self.screen_width = screen_width
        self.screen_height = screen_height

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
        half_width = self.screen_width / (2 * self.zoom)
        half_height = self.screen_height / (2 * self.zoom)

        min_x = half_width
        max_x = self.world_width - half_width

        min_y = half_height
        max_y = self.world_height - half_height

        self.position.x = max(min_x, min(self.position.x, max_x))
        self.position.y = max(min_y, min(self.position.y, max_y))

    def get_min_zoom(self):
        return max(
            self.screen_width / self.world_width, self.screen_height / self.world_height
        )

    def set_screen_size(self, new_w, new_h):
        self.screen_width = new_w
        self.screen_height = new_h

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
        self.position.x = self.world_width / 2
        self.position.y = self.world_height / 2

    def world_to_screen(self, world_position):
        relative = world_position - self.position

        return Vector2(
            relative.x * self.zoom + self.screen_width / 2,
            relative.y * self.zoom + self.screen_height / 2,
        )

    def screen_to_world(self, screen_position):
        if type(screen_position) == Vector2:
            spos_x, spos_y = screen_position.x, screen_position.y
        elif type(screen_position) == tuple:
            spos_x, spos_y = screen_position

        return Vector2(
            (spos_x - self.screen_width / 2) / self.zoom + self.position.x,
            (spos_y - self.screen_height / 2) / self.zoom + self.position.y,
        )

    def world_to_screen_tuple(self, world_position):
        relative = (
            world_position[0] - self.position.x,
            world_position[1] - self.position.y,
        )

        return (
            relative[0] * self.zoom + self.screen_width / 2,
            relative[1] * self.zoom + self.screen_height / 2,
        )


class Renderer:
    def __init__(
        self,
        gamestate,
        simulation,
        width=1920,
        height=1080,
        win_title="Akashic Renderer",
        background="#0C0C0E",
    ):
        if not gamestate.state["quiet"]:
            print("Initialising Renderer...")
        self.gamestate = gamestate.state

        self.width = width
        self.height = height
        self.simulation = simulation
        self.background = background

        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption(win_title)

        self.font = pygame.font.SysFont(
            ["JetBrains Mono Nerd Font", "JetBrains Mono", "monospace"],
            16,
        )

        self.camera = Camera(
            world_width=simulation.width,
            world_height=simulation.height,
            screen_width=self.width,
            screen_height=self.height,
        )

    def draw_vector(self, origin, vector, color):
        """Draw a given vector as a color colored arrow with origin as origin"""

        if vector.length() == 0:
            return

        end = origin + vector

        direction = vector.normalize()
        perpendicular = Vector2(-direction.y, direction.x)

        head_length = 6
        head_width = 2

        left = end - direction * head_length + perpendicular * head_width
        right = end - direction * head_length - perpendicular * head_width

        start_screen = self.camera.world_to_screen(origin)
        end_screen = self.camera.world_to_screen(end)
        left_screen = self.camera.world_to_screen(left)
        right_screen = self.camera.world_to_screen(right)

        pygame.draw.aaline(
            self.screen,
            color,
            (int(start_screen.x), int(start_screen.y)),
            (int(end_screen.x), int(end_screen.y)),
            2,
        )

        pygame.draw.polygon(
            self.screen,
            color,
            [
                (int(end_screen.x), int(end_screen.y)),
                (int(left_screen.x), int(left_screen.y)),
                (int(right_screen.x), int(right_screen.y)),
            ],
        )

    def draw_boid(self, boid):

        focused = self.gamestate["focus"] == boid

        boid_screen_position = self.camera.world_to_screen(boid.position)
        direction = boid.velocity.normalize()

        # Boid body
        tip = boid.position + direction * 12
        back = boid.position - direction * 8
        perpendicular = Vector2(-direction.y, direction.x)
        left = back + perpendicular * 6
        right = back - perpendicular * 6

        tip = self.camera.world_to_screen(tip)
        left = self.camera.world_to_screen(left)
        right = self.camera.world_to_screen(right)

        body_points = [
            (int(tip.x), int(tip.y)),
            (int(left.x), int(left.y)),
            (int(boid_screen_position.x), int(boid_screen_position.y)),
            (int(right.x), int(right.y)),
        ]

        # Boid sensor
        if focused or self.gamestate["boids_show_sensor"]:

            radius = boid.sensor_range * self.camera.zoom

            pygame.draw.circle(
                self.screen,
                "#444444",
                (int(boid_screen_position.x), int(boid_screen_position.y)),
                radius,
                1,
            )

        # Boid neighbors
        if focused:
            neighbors = self.simulation.get_neighbors(boid)
            candidates = self.simulation.grid.get_local_agents(boid.position)

            for candidate in candidates:
                if candidate is boid:
                    continue
                c_pos = self.camera.world_to_screen(candidate.position)
                pygame.draw.line(
                    self.screen,
                    "#CBCBCB" if candidate in neighbors else "#393939",
                    (int(boid_screen_position.x), int(boid_screen_position.y)),
                    (int(c_pos.x), int(c_pos.y)),
                    2 if candidate in neighbors else 1,
                )

            for neighbor in neighbors:
                if neighbor is boid:
                    continue
                n_pos = self.camera.world_to_screen(neighbor.position)
                pygame.draw.line(
                    self.screen,
                    "#CBCBCB",
                    (int(boid_screen_position.x), int(boid_screen_position.y)),
                    (int(n_pos.x), int(n_pos.y)),
                    1,
                )

        # Draw boid body
        pygame.draw.polygon(
            self.screen, "#C51313" if focused else boid.color, body_points
        )

        # Vectors
        if focused:
            self.draw_vector(boid.position, boid.velocity, "#EDAA46")

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
            x = self.width - text.get_width() - margin
            y = self.height - (len(lines) - i) * line_height - margin
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
            y = self.height - (full_height - i) * line_height - margin

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

            x = self.width - text.get_width() - margin
            y = i * line_height + margin

            self.screen.blit(text, (x, y))

    def draw_entity(self, bid):

        entities = self.simulation.entities
        focused = self.gamestate["focus"] == bid

        position = entities.positions[bid]
        screen_pos_x, screen_pos_y = self.camera.world_to_screen_tuple(position)
        velocity = entities.velocities[bid]

        speed = (velocity[0] ** 2 + velocity[1] ** 2) ** 0.5
        direction = velocity / speed

        if focused:
            # Draw neigbor lines
            nbs = self.simulation.get_neighbors(bid)
            print(nbs)
            for nib in nbs:
                nx, ny = self.camera.world_to_screen_tuple(entities.positions[nib])
                pygame.draw.line(
                    self.screen,
                    "#CBCBCB",
                    (int(screen_pos_x), int(screen_pos_y)),
                    (int(nx), int(ny)),
                    1,
                )

        # Draw boid body
        tip = position + direction * 12
        back = position - direction * 8
        perpendicular = np.array([-direction[1], direction[0]])
        left = back + perpendicular * 6
        right = back - perpendicular * 6

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
        if self.gamestate["focus"] and (
            self.gamestate["focus_boid_go_left"]
            or self.gamestate["focus_boid_go_right"]
        ):
            focused = self.gamestate["focus"]
            vel = self.simulation.entities.velocities[focused]
            perp = Vector2(vel.y, -vel.x).normalize()
            if self.gamestate["focus_boid_go_left"]:
                self.gamestate["focus_boid_go_direction"] = perp * vel.length()
            if self.gamestate["focus_boid_go_right"]:
                self.gamestate["focus_boid_go_direction"] = -perp * vel.length()

            if (
                not self.gamestate["focus_boid_go_left"]
                and not self.gamestate["focus_boid_go_right"]
            ):
                self.gamestate["focus_boid_go_direction"] = None

        # Clearing focus
        if self.gamestate["boids_clear_focus"]:
            self.gamestate["focus"] = None

        # WINDOW ####
        # Resizing
        if self.gamestate["win_resize"]:
            new_w, new_h = self.gamestate["win_resize"]
            self.width = new_w
            self.height = new_h
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
            boidname = str(len(self.simulation.boids) + 2)
            self.simulation.boids.append(
                Boid(
                    name=boidname,
                    x=randint(0, self.simulation.width - 1),
                    y=randint(0, self.simulation.height - 1),
                )
            )
            self.gamestate["boids_count"] += 1
        if self.gamestate["boids_rem"]:
            if self.gamestate["boids_count"] > 0:
                if self.gamestate["focus"] == self.simulation.boids.pop():
                    self.gamestate["focus"] = None
                self.gamestate["boids_count"] -= 1

    def draw(self, fps):
        """Read game state to know what and how to draw it"""

        self.screen.fill(self.background)

        if self.gamestate["focus_on"]:
            self.gamestate["focus"] = self.simulation.find_boid_at(
                self.camera.screen_to_world(self.gamestate["focus_on"])
            )
            self.gamestate["focus_on"] = None

        if self.gamestate["focus"] is not None:
            self.camera.focus_on(
                *self.simulation.entities.positions[self.gamestate["focus"]]
            )

        for bid in range(0, self.simulation.entities.count):
            self.draw_entity(bid)

        if self.gamestate["focus"] is not None:
            self.draw_focused_data(self.gamestate["focus"])

        if self.gamestate["show_debug"]:
            self.draw_debug(self.camera, fps)

        if self.gamestate["show_state"]:
            self.draw_state()

        pygame.display.flip()

    def save_state(self, dest=SAVE_STATE_FILE, force_write=False):
        # TODO: refactor for numpy
        or_stem = dest.stem
        dest.parent.mkdir(parents=True, exist_ok=True)

        i = 1
        while force_write or dest.exists():
            file_name = f"{or_stem}{i}{dest.suffix}"
            dest = dest.parent / file_name
            i += 1

        state = {
            "state": {
                k: (
                    {"name": v.name, "species": v.species}
                    if k == "focus" and v is not None
                    else (
                        tuple(v)
                        if k == "focus_boid_go_direction" and v is not None
                        else v
                    )
                )
                for k, v in self.gamestate.items()
            },
            "world": (self.simulation.width, self.simulation.height),
            "boids": [
                {
                    "name": boid.name,
                    "species": boid.species,
                    "position": tuple(boid.position),
                    "velocity": tuple(boid.velocity),
                    "acceleration": tuple(boid.acceleration),
                    "color": boid.color,
                }
                for boid in self.simulation.boids
            ],
        }

        with open(dest, "w") as file:
            json.dump(state, file, indent=4)
