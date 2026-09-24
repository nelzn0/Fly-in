#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   renderer.py                                          :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: nda-roch <nda-roch@student.42porto.com>      +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/18 17:32:51 by nda-roch            #+#    #+#            #
#   Updated: 2026/09/24 14:33:12 by nda-roch           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

from parser import ParsedMap
import pygame
from models import Hub, Connection

SCENE_FIT = 0.7
FONT_FRACTION = 8
HUB_FRACTION = 5
DRONE_FRACTION = 12
CONNECTION_FRACTION = 50


class Renderer:
    """
    Renderer class
    """

    def __init__(self, parsed: ParsedMap, trace: list[str]) -> None:
        """Renderer Parameters

        Arguments:
            parsed -- _description_
            trace -- _description_
        """
        xs = [hub.x for hub in parsed.hubs.values()]
        ys = [hub.y for hub in parsed.hubs.values()]
        self.parsed = parsed
        self.trace = trace
        self.connections = {"-".join(sorted([connection.hub1.name, connection.hub2.name]))                            : connection for connection in self.parsed.connections}
        self.max_x = max(xs)
        self.max_y = max(ys)
        self.min_x = min(xs)
        self.min_y = min(ys)
        self.screen = pygame.display.set_mode((1920, 1080))
        self.clock = pygame.time.Clock()
        self.palette = ["green", "blue", "yellow", "orange"]
        scene_width = self.max_x - self.min_x
        scene_height = self.max_y - self.min_y
        cell_w = SCENE_FIT * self.screen.get_width() // scene_width  # 70% of the screen width
        cell_h = SCENE_FIT * self.screen.get_height() // scene_height  # 70% of the screen height
        self.CELL_SIZE = int(min(cell_w, cell_h))
        self.margin_x = (self.screen.get_width() - (scene_width * self.CELL_SIZE)) // 2
        self.margin_y = (self.screen.get_height() - (scene_height * self.CELL_SIZE)) // 2
        font_size = int(self.CELL_SIZE // FONT_FRACTION)
        self.font = pygame.font.SysFont("arial", font_size)
        self.line_height = self.font.size("Ag")[1]  # max height = A, min height = g, [1] for only the height
        self.gap = self.line_height // 2  # line gap
        self.hub_radius = int(self.CELL_SIZE // HUB_FRACTION)
        self.drone_radius = int(self.CELL_SIZE // DRONE_FRACTION)
        self.connection_radius = int(self.CELL_SIZE // CONNECTION_FRACTION)

    def hub_to_pixel(self, hub: Hub) -> tuple[int, int]:
        """
        Returns the pixel position of the hub

        """
        px = (hub.x - self.min_x) * self.CELL_SIZE + self.margin_x
        py = (hub.y - self.min_y) * self.CELL_SIZE + self.margin_y
        return (px, py)

    def connection_to_pixel(self, connection: Connection) -> tuple[int, int]:
        """
        Returns the midpoint pixel of the connection

        """
        ax, ay = self.hub_to_pixel(connection.hub1)
        bx, by = self.hub_to_pixel(connection.hub2)
        px, py = (ax + bx) // 2, (ay + by) // 2
        return (px, py)

    def draw_frame(self, turn_index: int):
        """
            draw the hubs, the connections, and the drones

        """
        self.screen.fill("black")

        for hub in self.parsed.hubs.values():
            px, py = self.hub_to_pixel(hub)

            pygame.draw.circle(self.screen, hub.color or "white", (px, py), self.hub_radius)

            name_surface = self.font.render(hub.name, True, "white")
            name_x = px - name_surface.get_width() // 2
            name_y = py + self.hub_radius + self.gap
            self.screen.blit(name_surface, (name_x, name_y))

            type_surface = self.font.render(hub.zone_type, True, "white")

            type_x = px - type_surface.get_width() // 2
            type_y = name_y + self.line_height

            self.screen.blit(type_surface, (type_x, type_y))

        for connection in self.parsed.connections:
            ax, ay = self.hub_to_pixel(connection.hub1)
            bx, by = self.hub_to_pixel(connection.hub2)
            pygame.draw.line(self.screen, "blue", (ax, ay), (bx, by), self.connection_radius)

        for move in self.trace[turn_index].split():
            drone_id, location = move.split("-", 1)
            if location in self.parsed.hubs:
                px, py = self.hub_to_pixel(self.parsed.hubs[location])
            else:
                loc_h1, loc_h2 = location.split("-", 1)
                loc_key = "-".join(sorted([loc_h1, loc_h2]))
                conn = self.connections[loc_key]
                px, py = self.connection_to_pixel(conn)
            color = self.palette[int(drone_id[1:]) % len(self.palette)]

            pygame.draw.circle(self.screen, color, (px, py), self.drone_radius)

            drone_surface = self.font.render(drone_id, True, "white")

            drone_x = px - drone_surface.get_width() // 2
            drone_y = py - self.drone_radius - self.gap * 4

            self.screen.blit(drone_surface, (drone_x, drone_y))

        text_surface = self.font.render(f"Turn {turn_index}", True, "white")

        self.screen.blit(text_surface, (10, 10))

        pygame.display.flip()


def run_renderer(parsed: ParsedMap, trace: list[str]) -> None:
    """
    Constructs the renderer, and loops the frame drawing, paces the clock and advances the turns

    """
    pygame.init()
    running = True

    last_advance = pygame.time.get_ticks()
    BEAT_MS = 700
    render = Renderer(parsed, trace)
    turn_index = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        render.draw_frame(turn_index)
        render.clock.tick(30)

        if turn_index < len(trace) - 1:
            time_now = pygame.time.get_ticks()
            if time_now - last_advance >= BEAT_MS:
                turn_index += 1
                last_advance = time_now

    pygame.quit()
