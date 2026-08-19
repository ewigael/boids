import pygame

from .vector2 import Vector2


class Camera:
    def __init__(
        self,
        game_state,
        position,
        speed,
        world_width,
        world_height,
        screen_width,
        screen_height,
        zoom=1.0,
    ):
        """position refers to the simulation's world coordinates"""
        self.game_state = game_state
        self.position = position
        self.speed = speed
        self.zoom = zoom

        self.min_zoom = min(
            screen_width / world_width,
            screen_height / world_height,
        )

        self.world_width = world_width
        self.world_height = world_height
        self.screen_width = screen_width
        self.screen_height = screen_height

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

    def move(self, movement):
        self.position += movement
        self.clamp_position()

    def set_zoom(self, zoom):
        self.zoom = max(self.min_zoom, zoom)

        if self.zoom == self.min_zoom:
            self.center_on_world()
        else:
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

    def handle_inputs(self, dt):

        # Handle camera repositionning
        movement = Vector2(0, 0)
        if self.game_state.state["camera_move_left"]:
            movement.x -= 1
        if self.game_state.state["camera_move_right"]:
            movement.x += 1
        if self.game_state.state["camera_move_up"]:
            movement.y -= 1
        if self.game_state.state["camera_move_down"]:
            movement.y += 1

        camera_movement = movement.length()
        if camera_movement > 0:
            if camera_movement > 1:
                self.move(movement.normalize() * self.speed * dt)
            else:
                self.move(movement * self.speed * dt)

        # Handle camera zooming
        if self.game_state.state["camera_zoom_up"]:
            self.zoom_by(1 + 2 * dt)
        if self.game_state.state["camera_zoom_down"]:
            self.zoom_by(1 - 2 * dt)


class Renderer:
    def __init__(self, game_state, width, height, simulation, background="#0C0C0E"):
        self.game_state = game_state
        self.width = width
        self.height = height
        self.simulation = simulation
        self.background = background

        self.screen = pygame.display.set_mode((width, height))
        self.font = pygame.font.Font(None, 24)

        self.camera = Camera(
            game_state=game_state,
            position=Vector2(self.width / 2, self.height / 2),
            speed=1000,
            world_width=simulation.width,
            world_height=simulation.height,
            screen_width=self.width,
            screen_height=self.height,
        )

    def draw_boid(self, boid):

        focused = self.game_state.state["focus"] == boid

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
            (int(right.x), int(right.y)),
        ]

        # Boid sensor
        if focused or self.game_state.state["boids_show_sensor"]:

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
            for neighbor in self.simulation.get_neighbors(boid):
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

        # Draw boid body last
        pygame.draw.polygon(
            self.screen, "#C51313" if focused else boid.color, body_points
        )

    def draw_debug(self, camera, fps):
        lines = [
            f"FPS: {fps:.1f}",
            f"Camera: ({camera.position.x:.1f}, {camera.position.y:.1f})",
            f"Zoom: {camera.zoom:.2f}x",
        ]

        margin = 10
        line_height = self.font.get_height() + 3

        for i, line in enumerate(lines):
            text = self.font.render(line, True, "white")

            x = self.width - text.get_width() - margin
            y = self.height - (len(lines) - i) * line_height - margin

            self.screen.blit(text, (x, y))

    def draw_state(self):

        hidden_values = ["quit", "show_state"]

        margin = 10
        line_height = self.font.get_height() + 3
        full_height = len(self.game_state.state) - len(hidden_values)

        i = 0
        for line, value in self.game_state.state.items():
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

    def handle_inputs(self, dt):

        # CAMERA ####
        # Repositionning
        movement = Vector2(0, 0)
        if self.game_state.state["camera_move_left"]:
            movement.x -= 1
        if self.game_state.state["camera_move_right"]:
            movement.x += 1
        if self.game_state.state["camera_move_up"]:
            movement.y -= 1
        if self.game_state.state["camera_move_down"]:
            movement.y += 1

        camera_movement = movement.length()
        if camera_movement > 0:
            if camera_movement > 1:
                self.camera.move(movement.normalize() * self.camera.speed * dt)
            else:
                self.camera.move(movement * self.camera.speed * dt)

        # Zooming
        if self.game_state.state["camera_zoom_up"]:
            self.camera.zoom_by(1 + 2 * dt)
        if self.game_state.state["camera_zoom_down"]:
            self.camera.zoom_by(1 - 2 * dt)

        # FOCUS ####
        # Focusing
        if self.game_state.state["boids_focus_next"]:
            if self.game_state.state["focus"]:
                self.game_state.state["focus"] = self.simulation.boids[
                    (self.simulation.boids.index(self.game_state.state["focus"]) + 1)
                    % len(self.simulation.boids)
                ]
            else:
                self.game_state.state["focus"] = self.simulation.boids[0]

            self.camera.set_zoom(3)

        # Clearing focus
        if self.game_state.state["boids_clear_focus"]:
            self.game_state.state["focus"] = None

    def draw(self, fps):
        self.screen.fill(self.background)

        if self.game_state.state["focus"]:
            self.camera.focus_on(self.game_state.state["focus"])

        for boid in self.simulation.boids:
            self.draw_boid(boid)

        if self.game_state.state["show_debug"]:
            self.draw_debug(self.camera, fps)
        if self.game_state.state["show_state"]:
            self.draw_state()

        pygame.display.flip()
