"""Reads a map file and checks that it follows the rules."""

from dataclasses import dataclass
from models import Hub, Connection
from exceptions import ParseError


@dataclass
class ParsedMap:
    """The whole map after parsing, ready for the simulation.

    Attributes:
        hubs: All the zones on the map, by name.
        start: The start zone.
        end: The end zone.
        n_drones: How many drones to send.
        connections: All the connections between the zones.
    """

    hubs: dict[str, Hub]
    start: Hub
    end: Hub
    n_drones: int
    connections: list[Connection]


# the zone types a map is allowed to use
ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}


class Parser:
    """Turns the lines of a map file into a ParsedMap.

    The parser keeps what it has read so far. So use one Parser for one
    file only.

    Attributes:
        hubs: The zones read so far, by name.
        start_hub: The start zone, or None if it is not read yet.
        end_hub: The end zone, or None if it is not read yet.
        n_drones: The number from the nb_drones line.
        connections: The connections read so far.
        current_line_n: The number of the line being read, for errors.
        _seen_connections: The ids of the connections read so far, used to
            catch duplicates.
    """

    def __init__(self) -> None:
        """Creates an empty parser, with nothing read yet."""
        self.hubs: dict[str, Hub] = {}
        self.start_hub: Hub | None = None
        self.end_hub: Hub | None = None
        self.n_drones: int = 0
        self.connections: list[Connection] = []
        self.current_line_n: int = 0
        self._seen_connections: set[str] = set()

    def _parse_hub(self, rest: str) -> Hub:
        """Builds a Hub from the text after the prefix.

        It expects "name x y", and optional metadata in brackets, like
        "roof1 3 4 [zone=restricted color=red]". The metadata can come in
        any order. Nothing is stored here, the caller does that.

        Args:
            rest: The text after "hub:", already stripped.

        Returns:
            The new Hub, with its zone type, color and max_drones set.

        Raises:
            ParseError: If the name, the coordinates or the metadata are
                wrong.
        """

        # everything before "[" is the name and the coordinates
        if "[" in rest:
            main_part, metadata_part = rest.split("[", 1)
        else:
            main_part = rest
            metadata_part = None

        components = main_part.strip().split()
        if not components:
            raise ParseError(self.current_line_n, "Missing hub name")
        name = components[0]
        # a zone needs exactly a name, an x and a y
        if len(components) == 3:
            try:
                x = int(components[1])
                y = int(components[2])
            except ValueError:
                raise ParseError(
                    self.current_line_n,
                    f"Invalid coordinate in hub '{name}'. Expected integers, "
                    f"got '{components[1]}' and '{components[2]}'")

            # the defaults, used when the metadata doesn't say otherwise
            zone_type = "normal"
            color = None
            max_drones = 1

            # metadata is optional, so only check it when it is there
            if metadata_part:
                metadata_str = metadata_part.rstrip("]")

                for pair in metadata_str.split():
                    if "=" not in pair:
                        raise ParseError(
                            self.current_line_n,
                            f"Invalid metadata: '{pair}', expected "
                            "key=value, example: [max_drones=2]")
                    key, value = pair.split("=", 1)
                    if key == "zone":
                        if value.lower() not in ZONE_TYPES:
                            raise ParseError(
                                self.current_line_n,
                                f"'{value}' is not a valid zone!")
                        zone_type = value.lower()
                    elif key == "color":
                        color = value
                    elif key == "max_drones":
                        try:
                            if int(value) <= 0:
                                raise ParseError(
                                    self.current_line_n,
                                    "Invalid max_drones capacity")
                            max_drones = int(value)
                        # int() raises ValueError for text like "abc"
                        except ValueError:
                            raise (ParseError(
                                self.current_line_n,
                                "expecting a int for the key value"))
                    else:
                        raise ParseError(
                            self.current_line_n, f"'{key}' is not valid!")
        else:
            if len(components) < 3:
                raise ParseError(
                    self.current_line_n, f"Missing components for '{name}'")
            else:
                raise ParseError(
                    self.current_line_n,
                    f"'{name}' has too many fields, expected "
                    "(name x y [metadata])")

        return Hub(
            name=name,
            x=x,
            y=y,
            zone_type=zone_type,
            max_drones=max_drones,
            color=color
        )

    def _store_hub(self, hub: Hub) -> None:
        """Adds a zone to the map, as long as its name is new.

        Args:
            hub: The zone to store.

        Raises:
            ParseError: If a zone with the same name is already stored.
        """
        if hub.name in self.hubs:
            raise ParseError(
                self.current_line_n, f"Duplicate hub name '{hub.name}'")
        self.hubs[hub.name] = hub

    def _parse_connection(self, rest: str) -> Connection:
        """Builds a Connection from the text after the prefix.

        It expects "hub1-hub2", and optional metadata in brackets, like
        "corridorA-tunnelB [max_link_capacity=2]". Both zones must be read
        already. The new connection is added to both zones' lists.

        Args:
            rest: The text after "connection:", already stripped.

        Returns:
            The new Connection.

        Raises:
            ParseError: If the names, the zones or the metadata are wrong,
                or if the connection was already read.
        """
        # same split as in _parse_hub, everything before "[" is the link
        if "[" in rest:
            main_part, metadata_part = rest.split("[", 1)
        else:
            main_part = rest
            metadata_part = None
        # a link needs a dash between the two zone names
        if "-" not in main_part:
            raise ParseError(
                self.current_line_n,
                f"Invalid connection: '{main_part}', example: 'hub1-hub2'")
        components = main_part.strip().split("-")
        if len(components) != 2:
            raise ParseError(
                self.current_line_n,
                f"Invalid connection: '{main_part}', "
                "Connection must follow this format 'hub1-hub2'")
        if components[0] == components[1]:
            raise ParseError(
                self.current_line_n,
                f"Invalid connection: '{main_part}', "
                "Connection links its own hub")
        if components[0] in self.hubs and components[1] in self.hubs:
            hub1 = self.hubs[components[0]]
            hub2 = self.hubs[components[1]]

            # sort the names, so a-b and b-a give the same id
            names = [components[0], components[1]]
            names.sort()
            connection_id = "-".join(names)

            if connection_id in self._seen_connections:
                raise ParseError(
                    self.current_line_n,
                    f"Duplicate connection: {connection_id}")

            self._seen_connections.add(connection_id)

        else:
            if components[0] not in self.hubs:
                raise ParseError(
                    self.current_line_n,
                    f"Unknown hub '{components[0]}' in connection "
                    f"'{main_part.strip()}'")
            else:
                raise ParseError(
                    self.current_line_n,
                    f"Unknown hub '{components[1]}' in connection "
                    f"'{main_part.strip()}'")

        # the default, used when there is no metadata
        max_link_capacity = 1

        if metadata_part:
            metadata_str = metadata_part.rstrip("]")
            if "=" not in metadata_str:
                raise ParseError(
                    self.current_line_n,
                    f"Invalid metadata: '{metadata_str}', expected "
                    "key=value, example: [max_link_capacity=1]")
            name, value = metadata_str.split("=", 1)
            if name == "max_link_capacity":
                try:
                    if int(value) <= 0:
                        raise ParseError(
                            self.current_line_n,
                            "Invalid max_link_capacity")
                    max_link_capacity = int(value)
                # int() raises ValueError for text like "abc"
                except ValueError:
                    raise ParseError(self.current_line_n,
                                     f"'{value}' is not a Integer!")
            else:
                raise ParseError(
                    self.current_line_n, f"'{name}' is not valid!")

        connection = Connection(
            hub1=hub1,
            hub2=hub2,
            max_link_capacity=max_link_capacity,
        )

        # both zones need to know about the link, so the pathfinder can use it
        hub1.connections.append(connection)
        hub2.connections.append(connection)

        return connection

    def parse(self, filepath: str) -> ParsedMap:
        """Reads the whole map file and checks it line by line.

        Empty lines and lines that start with # are skipped. Every other line
        starts with a prefix (nb_drones, start_hub, end_hub, hub or
        connection), then a colon.

        Args:
            filepath: The path of the map file.

        Returns:
            The finished map, once the whole file is valid.

        Raises:
            ParseError: If a line is wrong, or the map has no drones, no
                start zone or no end zone.
            FileNotFoundError: If the file does not exist.
        """
        try:
            with open(filepath, "r") as f:
                data = f.read()
        except UnicodeDecodeError:
            raise ParseError(None, f"'{filepath}' is not a valid text file")

        # go through the file one line at a time, starting at line 1
        for line_n, raw_line in enumerate(data.splitlines(), start=1):
            self.current_line_n = line_n
            line = raw_line.strip()

            # skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # split "prefix: rest" at the first colon
            prefix, _separator, rest = line.partition(":")
            rest = rest.strip()

            if prefix == "nb_drones":
                try:
                    self.n_drones = int(rest)
                except ValueError:
                    raise ParseError(self.current_line_n,
                                     f"'{rest}' is not a Integer!")
            elif prefix == "start_hub":
                hub = self._parse_hub(rest)
                # only one start zone is allowed
                if self.start_hub is not None:
                    raise ParseError(
                        self.current_line_n, "Multiple start hubs")
                self._store_hub(hub)
                self.start_hub = hub
                hub.is_start = True
            elif prefix == "end_hub":
                hub = self._parse_hub(rest)
                # only one end zone is allowed
                if self.end_hub is not None:
                    raise ParseError(self.current_line_n, "Multiple end hubs")
                self._store_hub(hub)
                self.end_hub = hub
                hub.is_end = True
            elif prefix == "hub":
                hub = self._parse_hub(rest)
                self._store_hub(hub)
            elif prefix == "connection":
                connection = self._parse_connection(rest)
                self.connections.append(connection)
            else:
                raise ParseError(self.current_line_n,
                                 f"Unknown line type at line: {prefix}")

        # the map needs drones, a start zone and an end zone
        if self.n_drones <= 0:
            raise ParseError(None,
                             f"Number of drones is {self.n_drones}")

        if self.start_hub is None:
            raise ParseError(self.current_line_n, "No start hub found!")

        if self.end_hub is None:
            raise ParseError(self.current_line_n, "No end hub found!")

        return ParsedMap(
            hubs=self.hubs,
            start=self.start_hub,
            end=self.end_hub,
            n_drones=self.n_drones,
            connections=self.connections
        )
