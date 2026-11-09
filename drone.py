"""A drone and where it is on its route."""

from dataclasses import dataclass, field
from models import Hub, Connection


@dataclass
class Drone:
    """One drone that flies from the start zone to the end zone.

    A drone is either standing in a zone, or flying along a connection
    toward a restricted zone.

    Attributes:
        id: The drone number, starting at 1.
        position: The zone the drone is in, or the link it is flying on.
        destination: The restricted zone a flying drone is heading to.
        is_delivered: True once the drone has reached the end zone.
        plan: The full path of zones, from the start to the end.
        plan_index: The index in plan of the zone the drone is in, or
            the zone it is heading to.
    """

    id: int
    position: Hub | Connection
    destination: Hub | None = None
    is_delivered: bool = False
    plan: list[Hub] = field(default_factory=list)
    plan_index: int = 0
