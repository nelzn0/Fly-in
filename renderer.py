
"""Draws the simulation in a pygame window.

It only shows what the simulation already decided. It reads the trace one
turn at a time and draws the map, the zones and the drones.
"""

from parser import ParsedMap
import pygame
from models import Hub, Connection
import math

# sizes are relative to the window or the cell size, so the drawing scales
SCENE_FIT = 0.85
FONT_FRACTION = 13
FONT_FLOOR = 14
HUB_FRACTION = 5
HUB_FLOOR = 8
DRONE_FRACTION = 12
DRONE_FLOOR = 4
CONNECTION_FRACTION = 50
LOD_MINIMAL = 100
BEAT_MS = 700  # how long a turn stays on screen in auto mode, in ms
FOOTER_HEIGHT = 40
HUD_HEIGHT = 80


# colours for the UI. hub colours come from the map instead.
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
    """Draws the map, the drones and the top and bottom bars.

    Attributes:
        parsed: The parsed map, with the zones and connections.
        trace: One string per turn, like "D1-roof1 D2-goal".
        screen: The pygame window.
        clock: Keeps the frame rate steady.
        palette: The colours the drones cycle through.
        connections: The connections by key, like "a-b".
        CELL_SIZE: How many pixels one map unit takes.
    """

    def __init__(self, parsed: ParsedMap, trace: list[str]) -> None:
        """Opens the window and works out the sizes for this map.

        Args:
            parsed: The parsed map, with the zones and connections.
            trace: The turns from Simulation.run().
        """

        pygame.init()

        self.parsed = parsed
        self.trace = trace
        self.connections = self._index_connections()
        info = pygame.display.Info()
        width = min(1280, int(info.current_w * 0.8))
        height = min(720, int(info.current_h * 0.8))
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        # picked so they don't look like the usual hub colours
        self.palette = ["#ff5c5c", "#5cc8ff", "#ffd45c", "#c77dff",
                        "#ff8fd8", "#ff9e3d", "#7dffb3"]

        self._set_bounds()
        self._set_cell_size()
        self._load_fonts()
        self._set_radius()
        self._set_margins()

    def _index_connections(self) -> dict[str, Connection]:
        """Builds a lookup of connections by their key, like "a-b"."""
        connections = {
            self.connection_key(connection.hub1.name, connection.hub2.name):
                connection
            for connection in self.parsed.connections
        }
        return connections

    def _set_bounds(self) -> None:
        """Finds the smallest and biggest x and y, so the map can be placed."""
        xs = [hub.x for hub in self.parsed.hubs.values()]
        ys = [hub.y for hub in self.parsed.hubs.values()]
        self.max_x = max(xs)
        self.max_y = max(ys)
        self.min_x = min(xs)
        self.min_y = min(ys)
        self.scene_width = self.max_x - self.min_x
        self.scene_height = self.max_y - self.min_y

    def _set_cell_size(self) -> None:
        """Works out the biggest cell size that fits the whole map.

        A cell is the space for one map unit (one x or y step). The map is
        drawn with this size, so it fits the window whatever the map size.
        """
        # the space left between the top bar and the bottom bar
        self.world_height = (self.screen.get_height()
                             - HUD_HEIGHT - FOOTER_HEIGHT)
        cell_w = (SCENE_FIT * self.screen.get_width()
                  // max(self.scene_width, 1))
        cell_h = SCENE_FIT * self.world_height // max(self.scene_height, 1)
        self.CELL_SIZE = int(min(cell_w, cell_h))

    def _load_fonts(self) -> None:
        """Loads the fonts and picks the level of detail.

        Small maps get full labels. If the cells are too small to read the
        labels, only the circles are drawn.
        """
        font_size = int(max(self.CELL_SIZE // FONT_FRACTION, FONT_FLOOR))
        self.font = pygame.font.SysFont("consolas", font_size)
        # max height = A, min height = g, [1] for only the height
        self.line_height = self.font.size("Ag")[1]
        self.gap = self.line_height // 2  # line gap
        self.lod = ("full" if self.CELL_SIZE >= LOD_MINIMAL else "minimal")
        self.hud_font = pygame.font.SysFont("consolas", 24)

    def _set_radius(self) -> None:
        """Sets the sizes of the circles, based on the cell size."""
        self.hub_radius = int(max(self.CELL_SIZE // HUB_FRACTION, HUB_FLOOR))
        self.drone_radius = int(
            max(self.CELL_SIZE // DRONE_FRACTION, DRONE_FLOOR))
        self.connection_radius = int(self.CELL_SIZE // CONNECTION_FRACTION)

    def _set_margins(self) -> None:
        """Centres the map in the space between the top and bottom bars."""
        caption_lines = 3 if self.lod == "full" else 0
        caption_height = (self.hub_radius + self.gap
                          + caption_lines * self.line_height)
        self.margin_x = (
            self.screen.get_width() - (self.scene_width * self.CELL_SIZE)
        ) // 2
        self.margin_y = HUD_HEIGHT + (
            self.world_height - (self.scene_height * self.CELL_SIZE)
            - caption_height
        ) // 2

    def _safe_color(self, name: str | None) -> pygame.Color:
        """Turns a colour name from the map into a pygame colour.

        Args:
            name: The colour name, or None if the zone has no colour.

        Returns:
            The colour, or white if the name is not valid.
        """
        try:
            return pygame.Color(name or "white")
        except ValueError:
            return pygame.Color("white")

    def hub_to_pixel(self, hub: Hub) -> tuple[int, int]:
        """
        Turns a zone's map coordinates into a pixel position on the screen.

        Args:
            hub: The zone to place.

        Returns:
            The x and y pixel of the zone.
        """
        px = (hub.x - self.min_x) * self.CELL_SIZE + self.margin_x
        py = (hub.y - self.min_y) * self.CELL_SIZE + self.margin_y
        return (px, py)

    def _ring_offset(self, index: int, count: int) -> tuple[float, float]:
        """Works out where one drone sits on a ring around its spot.

        Drones on the same spot are spread on a ring, so none of them hide
        behind the others.

        Args:
            index: The drone's place in the list, starting at 0.
            count: How many drones share the spot.

        Returns:
            The x and y offset in pixels from the centre of the spot.
        """
        # a single drone stays in the middle
        if count == 1:
            return (0.0, 0.0)
        ring = max(self.hub_radius, count * self.drone_radius / math.pi)
        angle = 2 * math.pi * index / count
        return (ring * math.cos(angle), ring * math.sin(angle))

    def connection_to_pixel(self, connection: Connection) -> tuple[int, int]:
        """
        Returns the middle of a connection, where its drones are drawn.

        Args:
            connection: The connection to find the middle of.

        Returns:
            The x and y pixel in the middle of the two zones.
        """
        ax, ay = self.hub_to_pixel(connection.hub1)
        bx, by = self.hub_to_pixel(connection.hub2)
        px, py = (ax + bx) // 2, (ay + by) // 2
        return (px, py)

    def connection_key(self, name1: str, name2: str) -> str:
        """Returns the key of the connection between two zones.

        The names are sorted, so "a-b" and "b-a" give the same key.

        Args:
            name1: The name of one zone.
            name2: The name of the other zone.

        Returns:
            The two names sorted and joined with a dash.
        """

        return "-".join(sorted([name1, name2]))

    def draw_hud(self, turn_index: int) -> None:
        """Draws the top bar with the turn number."""

        pygame.draw.rect(
            self.screen, COLORS["HUD_BG"],
            (0, 0, self.screen.get_width(), HUD_HEIGHT))

        text_surface = self.hud_font.render(
            f"Turn {turn_index}", True, COLORS["TEXT_BRIGHT"])

        text_y = (HUD_HEIGHT - text_surface.get_height()) // 2

        self.screen.blit(text_surface, (20, text_y))

    def draw_stats(self, turn_index: int) -> None:
        """Draws the delivered, in-flight and move counts on the top bar."""

        delivered = self.count_delivered(turn_index)
        occupants = self.build_occupants(turn_index)
        # a drone on a connection is flying toward a restricted zone
        in_flight = sum(
            len(drones) for key, drones in occupants.items()
            if key not in self.parsed.hubs)
        moves = len(self.trace[turn_index - 1].split()) if turn_index else 0

        text_surface = self.hud_font.render(
            f"Delivered {delivered}/{self.parsed.n_drones}  "
            f"In flight {in_flight}  Moves {moves}",
            True, COLORS["HUD_TEXT"]
        )

        text_x = self.screen.get_width() - text_surface.get_width() - 20
        text_y = (HUD_HEIGHT - text_surface.get_height()) // 2
        self.screen.blit(text_surface, (text_x, text_y))

    def draw_footer(self, auto: bool) -> None:
        """Draws the controls bar along the bottom of the window."""

        top = self.screen.get_height() - FOOTER_HEIGHT

        pygame.draw.rect(
            self.screen, COLORS["HUD_BG"],
            (0, top, self.screen.get_width(), FOOTER_HEIGHT))

        mode = "AUTO" if auto else "MANUAL"
        controls = "TAB: switch mode  R: reset  ESC: quit"
        if not auto:
            controls = "SPACE: next turn  " + controls
        text_surface = self.hud_font.render(
            f"{mode} | {controls}", True, COLORS["HUD_TEXT"])

        text_y = top + (FOOTER_HEIGHT - text_surface.get_height()) // 2
        self.screen.blit(text_surface, (20, text_y))

    def build_occupants(self, turn_index: int) -> dict[str, list[str]]:
        """Works out which drones are on which zone or connection.

        Frame 0 is the start, so every drone is in the start zone. Frame N
        shows the moves from trace[N - 1], because trace[0] is turn 1.

        Args:
            turn_index: The frame to show, from 0 to the number of turns.

        Returns:
            The drone names by zone name or connection key.
        """
        if turn_index == 0:
            drones = [f"D{i}" for i in range(1, self.parsed.n_drones + 1)]
            return {self.parsed.start.name: drones}
        occupants: dict[str, list[str]] = {}
        for move in self.trace[turn_index - 1].split():
            drone_id, location = move.split("-", 1)
            if location in self.parsed.hubs:
                key = location
            else:
                h1, h2 = location.split("-", 1)
                key = self.connection_key(h1, h2)
            occupants.setdefault(key, []).append(drone_id)

        return occupants

    def count_delivered(self, turn_index: int) -> int:
        """Counts the drones that have reached the end zone by this frame.

        Delivered drones stop showing up in the trace, so this counts the
        moves that end in the end zone.

        Args:
            turn_index: The frame to count up to.

        Returns:
            The number of delivered drones.
        """

        end_name = self.parsed.end.name
        return sum(
            1
            for turn in self.trace[:turn_index]
            for move in turn.split()
            if move.split("-", 1)[1] == end_name)

    def draw_hubs(self, occupants: dict[str, list[str]]) -> None:
        """Draws every zone as a circle.

        With the full view it also writes the zone name, the zone type and
        the drones inside it under the circle.

        Args:
            occupants: The drone names by zone name, for this frame.
        """

        for hub in self.parsed.hubs.values():
            px, py = self.hub_to_pixel(hub)

            pygame.draw.circle(
                self.screen, self._safe_color(hub.color),
                (px, py), self.hub_radius)

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
        """Draws every connection as a line, with the drones on it.

        Args:
            occupants: The drone names by connection key, for this frame.
        """

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
                    occ_c_surface = self.font.render(
                        occ_c_text, True, COLORS["TEXT_BRIGHT"])
                    px, py = self.connection_to_pixel(connection)
                    occ_c_x = px - occ_c_surface.get_width() // 2
                    occ_c_y = py + self.connection_radius + self.gap

                    self.screen.blit(occ_c_surface, (occ_c_x, occ_c_y))

    def draw_drones(self, occupants: dict[str, list[str]]) -> None:
        """Draws the drones on top of the zones and connections.

        Drones on the same spot are spread on a small ring, so you can see
        each one.

        Args:
            occupants: The drone names by zone name or connection key.
        """
        for key, drones in occupants.items():
            if key in self.parsed.hubs:
                px, py = self.hub_to_pixel(self.parsed.hubs[key])
            else:
                px, py = self.connection_to_pixel(self.connections[key])
            for i, drone_id in enumerate(drones):
                dx, dy = self._ring_offset(i, len(drones))
                color = self.palette[int(drone_id[1:]) % len(self.palette)]
                pygame.draw.circle(
                    self.screen, color,
                    (round(px + dx), round(py + dy)), self.drone_radius)

    def draw_frame(self, turn_index: int, auto: bool = True) -> None:
        """Draws one frame for the given turn.

        The background and bars go first, then the lines, the zones and the
        drones on top. Drawing in this order keeps everything visible.

        Args:
            turn_index: The frame to draw.
            auto: True if the turns advance on their own.
        """

        self.screen.fill(COLORS["BACKGROUND"])

        self.draw_hud(turn_index)

        self.draw_stats(turn_index)

        self.draw_footer(auto)

        occupants = self.build_occupants(turn_index)

        # lines first, so the zone circles are drawn on top of them
        self.draw_connections(occupants)

        self.draw_hubs(occupants)

        self.draw_drones(occupants)

        pygame.display.flip()

    def run(self) -> None:
        """Runs the window until it is closed or ESC is pressed.

        Each frame it handles the keys, moves the turn on in auto mode, and
        draws the frame. The clock keeps the loop at about 30 frames a second.
        """
        running = True
        # auto moves on its own, manual waits for SPACE
        auto = True
        last_turn = len(self.trace)
        last_advance = pygame.time.get_ticks()
        # how many turns are on screen, 0 is the start
        turn_index = 0

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        auto = not auto
                        last_advance = pygame.time.get_ticks()

                    elif event.key == pygame.K_SPACE and not auto:
                        turn_index = min(turn_index + 1, last_turn)

                    elif event.key == pygame.K_r:
                        turn_index = 0
                        last_advance = pygame.time.get_ticks()

                    elif event.key == pygame.K_ESCAPE:
                        running = False

            # in auto mode the next turn comes once a beat has passed
            if auto and turn_index < last_turn:
                time_now = pygame.time.get_ticks()
                if time_now - last_advance >= BEAT_MS:
                    turn_index += 1
                    last_advance = time_now

            self.draw_frame(turn_index, auto)
            self.clock.tick(30)

        pygame.quit()
