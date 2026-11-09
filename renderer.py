#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   renderer.py                                          :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: nda-roch <nda-roch@student.42porto.com>      +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/18 17:32:51 by nda-roch            #+#    #+#            #
#   Updated: 2026/09/24 19:28:54 by nda-roch           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

from parser import ParsedMap
import pygame
from models import Hub, Connection

SCENE_FIT = 0.85
FONT_FRACTION = 13
FONT_FLOOR = 14
HUB_FRACTION = 5
HUB_FLOOR = 8
DRONE_FRACTION = 12
DRONE_FLOOR = 4
CONNECTION_FRACTION = 50
LOD_MINIMAL = 100
BEAT_MS = 700

COLORS = {
    "BACKGROUND": "#0a0a12",
    "TEXT_BRIGHT": "white",
    "TEXT_DIM": "gray55",
    "TEXT_ACTIVE": "orange3",
    "LINES": "forestgreen",
    "HUD_BG": "gray20",
    "HUD_TEXT": "orange3",
}


class Renderer:
    """
    Renderer class
    """

    HUD_HEIGHT = 80

    def __init__(self, parsed: ParsedMap, trace: list[str]) -> None:
        """Renderer Parameters

        Arguments:
            parsed -- _description_
            trace -- _description_
        """

        pygame.init()

        self.parsed = parsed
        self.trace = trace
        self.connections = self._index_connections()
        self.screen = pygame.display.set_mode((1920, 1080))
        self.clock = pygame.time.Clock()
        self.palette = ["green", "blue", "yellow", "orange"]

        self._set_bounds()
        self._set_cell_size()
        self._load_fonts()
        self._set_radius()
        self._set_margins()

    def _index_connections(self) -> dict[str, Connection]:
        connections = {
            self.connection_key(connection.hub1.name, connection.hub2.name):
                connection
            for connection in self.parsed.connections
        }
        return connections

    def _set_bounds(self) -> None:
        xs = [hub.x for hub in self.parsed.hubs.values()]
        ys = [hub.y for hub in self.parsed.hubs.values()]
        self.max_x = max(xs)
        self.max_y = max(ys)
        self.min_x = min(xs)
        self.min_y = min(ys)
        self.scene_width = self.max_x - self.min_x
        self.scene_height = self.max_y - self.min_y

    def _set_cell_size(self) -> None:
        self.world_height = self.screen.get_height() - self.HUD_HEIGHT
        cell_w = (SCENE_FIT * self.screen.get_width()
                  // max(self.scene_width, 1))
        cell_h = SCENE_FIT * self.world_height // max(self.scene_height, 1)
        self.CELL_SIZE = int(min(cell_w, cell_h))

    def _load_fonts(self) -> None:
        font_size = int(max(self.CELL_SIZE // FONT_FRACTION, FONT_FLOOR))
        self.font = pygame.font.SysFont("consolas", font_size)
        # max height = A, min height = g, [1] for only the height
        self.line_height = self.font.size("Ag")[1]
        self.gap = self.line_height // 2  # line gap
        self.lod = ("full" if self.CELL_SIZE >= LOD_MINIMAL else "minimal")
        self.hud_font = pygame.font.SysFont("consolas", 24)

    def _set_radius(self) -> None:
        self.hub_radius = int(max(self.CELL_SIZE // HUB_FRACTION, HUB_FLOOR))
        self.drone_radius = int(
            max(self.CELL_SIZE // DRONE_FRACTION, DRONE_FLOOR))
        self.connection_radius = int(self.CELL_SIZE // CONNECTION_FRACTION)

    def _set_margins(self) -> None:
        caption_lines = 3 if self.lod == "full" else 0
        caption_height = (self.hub_radius + self.gap
                          + caption_lines * self.line_height)
        self.margin_x = (
            self.screen.get_width() - (self.scene_width * self.CELL_SIZE)
        ) // 2
        self.margin_y = self.HUD_HEIGHT + (
            self.world_height - (self.scene_height * self.CELL_SIZE)
            - caption_height
        ) // 2

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

    def connection_key(self, name1: str, name2: str) -> str:
        """Returns the identifier of the connection between two hubs (sorted)

        Arguments:
            name1 -- _description_
            name2 -- _description_

        Returns:
            _description_
        """

        return "-".join(sorted([name1, name2]))

    def draw_hud(self, turn_index: int) -> None:

        pygame.draw.rect(
            self.screen, COLORS["HUD_BG"],
            (0, 0, self.screen.get_width(), self.HUD_HEIGHT))

        text_surface = self.hud_font.render(
            f"Turn {turn_index}", True, "white")

        text_y = (self.HUD_HEIGHT - text_surface.get_height()) // 2

        self.screen.blit(text_surface, (20, text_y))

    def build_occupants(self, turn_index: int) -> dict[str, list[str]]:
        occupants: dict[str, list[str]] = {}
        for move in self.trace[turn_index].split():
            drone_id, location = move.split("-", 1)
            if location in self.parsed.hubs:
                key = location
            else:
                h1, h2 = location.split("-", 1)
                key = self.connection_key(h1, h2)
            occupants.setdefault(key, []).append(drone_id)

        return occupants

    def draw_hubs(self, occupants: dict[str, list[str]]) -> None:

        for hub in self.parsed.hubs.values():
            px, py = self.hub_to_pixel(hub)

            pygame.draw.circle(
                self.screen, hub.color or "white", (px, py), self.hub_radius)

            if self.lod == "full":

                name_surface = self.font.render(
                    hub.name, True, COLORS["TEXT_BRIGHT"])

                name_x = px - name_surface.get_width() // 2
                name_y = py + self.hub_radius + self.gap

                self.screen.blit(name_surface, (name_x, name_y))
                type_surface = self.font.render(
                    hub.zone_type, True, COLORS["TEXT_DIM"])

                type_x = px - type_surface.get_width() // 2
                type_y = name_y + self.line_height

                self.screen.blit(type_surface, (type_x, type_y))

                drones = occupants.get(hub.name, [])
                if drones:
                    if not (hub.is_end or hub.is_start):
                        occ_text = (f"{' '.join(drones)} "
                                    f"({len(drones)}/{hub.max_drones})")
                    else:
                        occ_text = ' '.join(drones)
                    occ_surface = self.font.render(
                        occ_text, True, COLORS["TEXT_ACTIVE"])
                    occ_x = px - occ_surface.get_width() // 2
                    occ_y = type_y + self.line_height
                    self.screen.blit(occ_surface, (occ_x, occ_y))

    def draw_connections(self, occupants: dict[str, list[str]]) -> None:

        for connection in self.parsed.connections:
            ax, ay = self.hub_to_pixel(connection.hub1)
            bx, by = self.hub_to_pixel(connection.hub2)
            pygame.draw.line(
                self.screen, COLORS["LINES"], (ax, ay), (bx, by),
                self.connection_radius)

            if self.lod == "full":

                link_key = self.connection_key(
                    connection.hub1.name, connection.hub2.name)
                drones_c = occupants.get(link_key, [])
                if drones_c:
                    if connection.max_link_capacity > 1:
                        occ_c_text = (
                            f"{' '.join(drones_c)} ({len(drones_c)}/"
                            f"{connection.max_link_capacity})")
                    else:
                        occ_c_text = " ".join(drones_c)
                    occ_c_surface = self.font.render(occ_c_text, True, "white")
                    px, py = self.connection_to_pixel(connection)
                    occ_c_x = px - occ_c_surface.get_width() // 2
                    occ_c_y = py + self.connection_radius + self.gap

                    self.screen.blit(occ_c_surface, (occ_c_x, occ_c_y))

    def draw_drones(self, occupants: dict[str, list[str]]) -> None:
        for key, drones in occupants.items():
            if key in self.parsed.hubs:
                px, py = self.hub_to_pixel(self.parsed.hubs[key])
            else:
                px, py = self.connection_to_pixel(self.connections[key])
            for drone_id in drones:
                color = self.palette[int(drone_id[1:]) % len(self.palette)]
                pygame.draw.circle(
                    self.screen, color, (px, py), self.drone_radius)

    def draw_frame(self, turn_index: int) -> None:
        """
            draw the hubs, the connections, and the drones

        """

        self.screen.fill(COLORS["BACKGROUND"])

        self.draw_hud(turn_index)

        occupants = self.build_occupants(turn_index)

        self.draw_hubs(occupants)

        self.draw_connections(occupants)

        self.draw_drones(occupants)

        pygame.display.flip()

    def run(self) -> None:
        """
        Constructs the renderer, and loops the frame drawing, paces the
        clock and advances the turns

        """
        running = True

        last_advance = pygame.time.get_ticks()
        turn_index = 0

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # if event.type == pygame.KEYDOWN:
                #     if event.key == pygame.K_SPACE:
                #         turn_index += 1

            self.draw_frame(turn_index)
            self.clock.tick(30)

            if turn_index < len(self.trace) - 1:
                time_now = pygame.time.get_ticks()
                if time_now - last_advance >= BEAT_MS:
                    turn_index += 1
                    last_advance = time_now

        pygame.quit()
