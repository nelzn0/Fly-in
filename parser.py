#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   parser.py                                            :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: nda-roch <nda-roch@student.42porto.com>      +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/08/27 14:44:15 by nda-roch            #+#    #+#            #
#   Updated: 2026/08/27 19:13:23 by nda-roch           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

from dataclasses import dataclass


@dataclass
class ParsedMap:
    hubs: dict[str, Hub]
    start: Hub
    end: Hub
    n_drones: int
    connections: list[Connection]


zones = {"normal", "blocked", "restricted", "priority"}


class Parser:
    def __init__(self) -> None:
        self.hubs: dict[str, Hub] = {}
        self.start_hub: Hub | None = None
        self.end_hub: Hub | None = None
        self.n_drones: int = 0
        self.connections: list[Connection] = []
        self.current_line_n: int = 0
        self._seen_connections: set[str] = set()

    def _parse_hub(self, rest: str) -> Hub:

        if "[" in rest:
            main_part, metadata_part = rest.split("[", 1)
        else:
            main_part = rest
            metadata_part = None

        components = main_part.strip().split(" ")
        name = components[0]
        if len(components) == 3:
            try:
                x = int(components[1])
                y = int(components[2])
            except ValueError:
                raise Exception(
                    f"Line {self.current_line_n}: Invalid coordinate in hub '{name}'. Expected integers, got '{components[1]}' and '{components[2]}'")

            metadata = {}
            if metadata_part:
                metadata_str = metadata_part.rstrip("]")

                for pair in metadata_str.split(" "):
                    key, value = pair.split("=")
                    if key == "max_drones":
                        if int(value) <= 0:
                            raise Exception(
                                f"Line {self.current_line_n}: Invalid max_drones capacity")
                        metadata[key] = int(value)
                    else:
                        metadata[key] = value

                    if key == "zone":
                        if value.lower() not in zones:
                            raise Exception(
                                f"Line {self.current_line_n}: '{value}' is not a valid zone!")
            else:
                raise Exception(
                    f"Line {self.current_line_n}: Missing components for '{name}'")

        return Hub(
            name=name,
            x=x,
            y=y,
            metadata=metadata
        )

    def _parse_connection(self, rest: str) -> Connection:
        if "[" in rest:
            main_part, metadata_part = rest.split("[", 1)
        else:
            main_part = rest
            metadata_part = None

        components = main_part.strip().split("-")
        if components[0] in self.hubs and components[1] in self.hubs:
            hub1 = self.hubs[components[0]]
            hub2 = self.hubs[components[1]]

            names = [components[0], components[1]]
            names.sort()
            connection_id = "-".join(names)

            if connection_id in self._seen_connections:
                raise Exception(
                    f"Line {self.current_line_n}: Duplicate connection: {connection_id}")

            self._seen_connections.add(connection_id)

        else:
            if components[0] not in self.hubs:
                raise Exception(
                    f"Line {self.current_line_n}: Unknown hub '{components[0]}' in connection '{main_part.strip()}'")
            else:
                raise Exception(
                    f"Line {self.current_line_n}: Unknown hub '{components[1]}' in connection '{main_part.strip()}'")

        metadata = {}
        if metadata_part:
            metadata_str = metadata_part.rstrip("]")
            name, value = metadata_str.split("=")
            if name == "max_link_capacity":
                try:
                    metadata[name] = int(value)
                except ValueError:
                    raise ValueError(
                        f"Line {self.current_line_n}: '{value}' is not a Integer!")
            else:
                raise Exception(
                    f"Line {self.current_line_n}: '{name}' is not valid!")

        return Connection(
            hub1=hub1,
            hub2=hub2,
            metadata=metadata
        )

    def parse(self, filepath: str) -> ParsedMap:
        with open(filepath, "r") as f:
            data = f.read()

        for line_n, raw_line in enumerate(data.splitlines(), start=1):
            self.current_line_n = line_n
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            prefix, _separator, rest = line.partition(":")
            rest = rest.strip()

            if prefix == "nb_drones":
                try:
                    self.n_drones = int(rest)
                except ValueError:
                    raise ValueError(
                        f"Line {self.current_line_n}: '{rest}' is not a Integer!")
            elif prefix == "start_hub":
                hub = self._parse_hub(rest)
                self.start_hub = hub
                self.hubs[hub.name] = hub
            elif prefix == "end_hub":
                hub = self._parse_hub(rest)
                self.end_hub = hub
                self.hubs[hub.name] = hub
            elif prefix == "hub":
                hub = self._parse_hub(rest)
                self.hubs[hub.name] = hub
            elif prefix == "connection":
                connection = self._parse_connection(rest)
                self.connections.append(connection)
            else:
                raise Exception(
                    f"Unknown line type at line {self.current_line_n}: {prefix}")

        if self.n_drones <= 0:
            raise Exception(f"Number of drones is {self.n_drones}")

        if self.start_hub is None:
            raise Exception("No start hub found!")

        if self.end_hub is None:
            raise Exception("No end hub found!")

        return ParsedMap(
            hubs=self.hubs,
            start=self.start_hub,
            end=self.end_hub,
            n_drones=self.n_drones,
            connections=self.connections
        )
