
"""Moves the drones turn by turn from the start to the end zone."""

from parser import ParsedMap
from drone import Drone
from models import Hub, Connection
from pathfinder import Pathfinder
from exceptions import SimulationError

# extra load added to a zone for each drone already planned through it
HUB_PENALTY = 0.5


class Simulation:
    """Plans the paths and then runs every turn until all drones arrive.

    Attributes:
        hubs: All the zones on the map, by name.
        start: The start zone.
        end: The end zone.
        drones: All the drones. They all start in the start zone.
        load: The planned load per zone name, used by the pathfinder.
        pathfinder: The object that finds the paths.
    """

    def __init__(self, parsed_map: ParsedMap) -> None:
        """Creates the drones and the pathfinder.

        Args:
            parsed_map: The map from the parser.
        """
        self.hubs = parsed_map.hubs
        self.start = parsed_map.start
        self.end = parsed_map.end
        self.drones = [Drone(id=i, position=parsed_map.start)
                       for i in range(1, parsed_map.n_drones + 1)]
        self.load: dict[str, float] = {
            hub.name: 0.0 for hub in parsed_map.hubs.values()}
        self.pathfinder = Pathfinder(self.hubs, self.start, self.end)

    def drone_paths(self) -> None:
        """Gives every drone its path before the turns start.

        The drones are planned one after another. After each path, every
        zone on it gets HUB_PENALTY more load. So the next drone looks for
        a different route, if there is one.
        """
        for drone in self.drones:
            path = self.pathfinder.find_path(self.load)
            drone.plan = path
            for hub in path:
                self.load[hub.name] += HUB_PENALTY

    def _can_enter_zone(self, next_hub: Hub) -> bool:
        """Checks if one more drone fits in a zone this turn.

        It counts the drones already in the zone, plus the drones flying
        toward it. The start and end zones have no limit.

        Args:
            next_hub: The zone the drone wants to enter.

        Returns:
            True if the drone is allowed in.
        """
        # drones standing in the zone right now
        occupants = sum(
            1 for d in self.drones if d.position == next_hub)
        # drones that are flying toward it, so the space is already taken
        reserved = sum(
            1 for d in self.drones if d.destination == next_hub)

        return (
            occupants + reserved + 1 <= next_hub.max_drones
            or next_hub.is_end
            or next_hub.is_start
        )

    def _can_use_link(
        self, conn: Connection, link_usage: dict[str, int]
    ) -> bool:
        """Checks if one more drone can use a connection this turn.

        It counts the drones flying on the link, plus the moves that were
        already planned on it this turn.

        Args:
            conn: The connection the drone wants to use.
            link_usage: How many drones started using each link this turn,
                by link name.

        Returns:
            True if the drone is allowed on the link.
        """
        on_link = sum(
            1 for d in self.drones if d.position is conn)
        key = "-".join(sorted([conn.hub1.name, conn.hub2.name]))

        return on_link + link_usage.get(key, 0) + 1 <= conn.max_link_capacity

    def _move_in_flight(self, drone: Drone) -> str:
        """Moves a drone that is flying toward a restricted zone.

        A restricted move goes into the link on one turn, and the drone
        lands on the next turn. This is the landing turn.

        Args:
            drone: A drone whose position is a connection.

        Returns:
            The move text for this turn. It is "D<id>-<zone>" when the
            drone lands.
        """
        if drone.destination is None:
            raise SimulationError(None, "Drone destination was not found")
        drone.position = drone.destination
        if drone.position == self.end:
            drone.is_delivered = True
        drone.destination = None
        return (f"D{drone.id}-{drone.position.name}")

    def _move_drone(
        self, drone: Drone, link_usage: dict[str, int]
    ) -> str | None:
        """Tries to move a drone one step forward along its plan.

        A normal or priority zone is entered on the same turn. A restricted
        zone is reached in two steps: the drone goes into the link now, and
        it lands on the next turn. The drone waits (returns None) if the
        zone or the link is full, or if it has already reached the end.

        Args:
            drone: A drone that is standing in a zone.
            link_usage: How many drones started using each link this turn,
                by link name. It is updated when the drone moves.

        Returns:
            The move text, or None if the drone stays where it is.
        """
        if drone.plan_index + 1 < len(drone.plan):
            next_hub = drone.plan[drone.plan_index + 1]
            # the connection between where the drone is and the next zone
            if not isinstance(drone.position, Hub):
                raise SimulationError(None, "Drone is not in a hub")
            conn = next(
                c for c in drone.position.connections
                if next_hub in (c.hub1, c.hub2))
            key = "-".join(sorted([conn.hub1.name, conn.hub2.name]))
            # restricted: the drone goes into the link now and lands next turn
            if next_hub.zone_type == "restricted":
                if (self._can_enter_zone(next_hub)
                        and self._can_use_link(conn, link_usage)):
                    drone.destination = next_hub
                    drone.position = conn
                    drone.plan_index += 1
                    link_usage[key] = link_usage.get(key, 0) + 1
                    return (
                        f"D{drone.id}-{conn.hub1.name}-{conn.hub2.name}")
            else:
                if (self._can_enter_zone(next_hub)
                        and self._can_use_link(conn, link_usage)):
                    drone.position = next_hub
                    drone.plan_index += 1
                    link_usage[key] = link_usage.get(key, 0) + 1
                    if drone.position == self.end:
                        drone.is_delivered = True
                    return (f"D{drone.id}-{drone.position.name}")
        return None

    def run(self) -> list[str]:
        """Runs the simulation turn by turn until every drone is delivered.

        Returns:
            One string per turn, with all the moves of that turn. For example
            "D1-roof1 D2-corridorA". Drones that don't move are left out.

        Raises:
            SimulationError: If no drone can move on a turn. The simulation
                would be stuck forever, so it stops.
        """
        trace: list[str] = []
        while not all(drone.is_delivered for drone in self.drones):
            moves = []
            # reset every turn, it only counts the moves of this turn
            link_usage: dict[str, int] = {}
            for drone in self.drones:
                # drones in the air keep flying, the others try to move
                if isinstance(drone.position, Connection):
                    moves.append(self._move_in_flight(drone))
                else:
                    move = self._move_drone(drone, link_usage)
                    if move:
                        moves.append(move)
            if not moves:
                raise SimulationError(None, "Drone could not move")
            trace.append(" ".join(moves))
        return trace
