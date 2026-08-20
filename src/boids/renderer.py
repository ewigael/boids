import pygame

from .vector2 import Vector2
from .perflog import PerformanceLogger

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

    def focus_on(self, boid):
        self.position.x = boid.position.x
        self.position.y = boid.position.y
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
        print("Initialising Renderer...")
        self.gamestate = gamestate.state

        self.gamestate["focus"] = None
        self.gamestate["show_debug"] = "fps_cam_perf"

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
            candidates = self.simulation.grid.get_local_agents(boid)

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
            for logger in PerformanceLogger.loggers:
                lines.append((f"Performance Logger #{logger.name}", "#D9D9D9"))
                for name, delta in logger.get_averages():
                    lines.append((f"{name} {delta:>9s}", "#D9D9D9"))

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

    def draw_focused_data(self, boid):
        lines = [
            f"Boid {id(boid)}",
            "",
            f"X {boid.position.x:8.2f}",
            f"Y {boid.position.y:8.2f}",
            f"Speed {boid.velocity.length():8.2f}",
            "",
            f"Neighbors:  {len(self.simulation.get_neighbors(boid))}",
            f"Candidates: {len(self.simulation.grid.get_local_agents(boid))}",
            "",
            f"Color: {boid.color}",
            f"Speed range: {boid.min_speed} {boid.max_speed}",
            "",
            f"ESC to unfocus",
        ]

        margin = 10
        line_height = self.font.get_height() + 3
        full_height = len(self.gamestate)

        for i, line in enumerate(lines):
            text = self.font.render(
                line,
                True,
                "#E5D68B",
            )

            x = self.width - text.get_width() - margin
            y = i * line_height + margin

            self.screen.blit(text, (x, y))

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

        # FOCUS ####
        # Focusing
        if self.gamestate["boids_focus_next"]:
            if self.gamestate["focus"]:
                self.gamestate["focus"] = self.simulation.boids[
                    (self.simulation.boids.index(self.gamestate["focus"]) + 1)
                    % len(self.simulation.boids)
                ]
            else:
                self.gamestate["focus"] = self.simulation.boids[0]

            self.camera.set_zoom(3)

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

    def draw(self, fps):
        """Read game state to know what and how to draw it"""

        self.screen.fill(self.background)

        if self.gamestate["focus"]:
            self.camera.focus_on(self.gamestate["focus"])

        for boid in self.simulation.boids:
            self.draw_boid(boid)

        if self.gamestate["focus"]:
            self.draw_focused_data(self.gamestate["focus"])

        if self.gamestate["show_debug"]:
            self.draw_debug(self.camera, fps)

        if self.gamestate["show_state"]:
            self.draw_state()

        pygame.display.flip()
