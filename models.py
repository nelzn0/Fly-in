
"""The zones (hubs) of the map and the connections between them."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Hub:
    """A zone on the map, the place where drones stop.

    Attributes:
        name: The name of the zone. It is unique on the map.
        x: The x coordinate of the zone.
        y: The y coordinate of the zone.
        zone_type: "normal", "restricted", "priority" or "blocked".
        max_drones: How many drones can be in the zone at the same time.
        color: The color from the map, or None if there isn't one.
        connections: The connections that touch this zone.
        is_start: True if this is the start zone.
        is_end: True if this is the end zone.
    """

    name: str
    x: int
    y: int
    zone_type: str              # "normal", "restricted", "priority", "blocked"
    max_drones: int = 1         # default 1, start/end unlimited
    color: str | None = None
    connections: list[Connection] = field(default_factory=list)
    is_start: bool = False
    is_end: bool = False


@dataclass
class Connection:
    """A link between two zones that drones can fly along.

    Attributes:
        hub1: One of the two zones.
        hub2: The other zone.
        max_link_capacity: How many drones can use the link at the same
            time.
    """

    hub1: Hub
    hub2: Hub
    max_link_capacity: int = 1
