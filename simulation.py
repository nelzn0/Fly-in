#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   simulation.py                                        :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: nda-roch <nda-roch@student.42porto.com>      +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/10 14:56:44 by nda-roch            #+#    #+#            #
#   Updated: 2026/09/23 19:43:49 by nda-roch           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

from parser import ParsedMap
from drone import Drone
from models import Hub, Connection
from pathfinder import Pathfinder
from exceptions import SimulationError

HUB_PENALTY = 0.5


class Simulation:
    def __init__(self, parsed_map: ParsedMap) -> None:
        self.hubs = parsed_map.hubs
        self.start = parsed_map.start
        self.end = parsed_map.end
        self.drones = [Drone(id=i, position=parsed_map.start)
                       for i in range(1, parsed_map.n_drones + 1)]
        self.load: dict[str, float] = {
            hub.name: 0.0 for hub in parsed_map.hubs.values()}
        self.pathfinder = Pathfinder(self.hubs, self.start, self.end)

    def drone_paths(self) -> None:
        for drone in self.drones:
            path = self.pathfinder.find_path(self.load)
            drone.plan = path
            for hub in path:
                self.load[hub.name] += HUB_PENALTY

    def _can_enter_zone(self, next_hub: Hub) -> bool:
        occupants = sum(
            1 for d in self.drones if d.position == next_hub)
        reserved = sum(
            1 for d in self.drones if d.destination == next_hub)

        return (occupants + reserved + 1 <= next_hub.max_drones or next_hub.is_end or next_hub.is_start)

    def _can_use_link(self, conn: Connection, link_usage: dict[str, int]) -> bool:
        on_link = sum(
            1 for d in self.drones if d.position is conn)
        key = "-".join(sorted([conn.hub1.name, conn.hub2.name]))

        return on_link + link_usage.get(key, 0) + 1 <= conn.max_link_capacity

    def _move_in_flight(self, drone: Drone) -> str:
        conn = drone.position
        drone.remaining_turns -= 1
        if drone.remaining_turns > 0:
            drone.position = drone.destination
            if drone.position == self.end:
                drone.is_delivered = True
            drone.destination = None
            return (f"D{drone.id}-{drone.position.name}")
        else:
            return (
                f"D{drone.id}-{conn.hub1.name}-{conn.hub2.name}")

    def _move_drone(self, drone: Drone, link_usage: dict[str, int]) -> str | None:
        if drone.plan_index + 1 < len(drone.plan):
            next_hub = drone.plan[drone.plan_index + 1]
            conn = next(
                c for c in drone.position.connections if next_hub in (c.hub1, c.hub2))
            key = "-".join(sorted([conn.hub1.name, conn.hub2.name]))
            if next_hub.zone_type == "restricted":
                if self._can_enter_zone(next_hub) and self._can_use_link(conn, link_usage):
                    drone.remaining_turns = 2
                    drone.destination = next_hub
                    drone.position = conn
                    drone.plan_index += 1
                    link_usage[key] = link_usage.get(key, 0) + 1
                    return (
                        f"D{drone.id}-{conn.hub1.name}-{conn.hub2.name}")
            else:
                if self._can_enter_zone(next_hub) and self._can_use_link(conn, link_usage):
                    drone.position = next_hub
                    drone.plan_index += 1
                    link_usage[key] = link_usage.get(key, 0) + 1
                    if drone.position == self.end:
                        drone.is_delivered = True
                    return (f"D{drone.id}-{drone.position.name}")
        return None

    def run(self) -> list[str]:
        trace: list[str] = []
        while not all(drone.is_delivered for drone in self.drones):
            moves = []
            link_usage = {}
            for drone in self.drones:
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
