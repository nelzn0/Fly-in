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
from pathfinder import find_path


class Simulation:
    def __init__(self, parsed_map: ParsedMap) -> None:
        self.hubs = parsed_map.hubs
        self.start = parsed_map.start
        self.end = parsed_map.end
        self.drones = [Drone(id=i, position=parsed_map.start)
                       for i in range(1, parsed_map.n_drones + 1)]
        self.connections = parsed_map.connections
        self.load: dict[str, float] = {
            hub.name: 0.0 for hub in parsed_map.hubs.values()}

    def drone_paths(self) -> None:
        for drone in self.drones:
            path = find_path(
                self.start, self.end, self.hubs, self.load)
            drone.plan = path
            for hub in path:
                self.load[hub.name] += 0.5

    def run(self) -> list[str]:
        trace: list[str] = []
        while not all(drone.is_delivered for drone in self.drones):
            moves = []
            link_usage = {}
            for drone in self.drones:
                if isinstance(drone.position, Connection):
                    conn = drone.position
                    drone.remaining_turns -= 1
                    if drone.remaining_turns > 0:
                        drone.position = drone.destination
                        drone.destination = None
                        moves.append(f"D{drone.id}-{drone.position.name}")
                    else:
                        moves.append(
                            f"D{drone.id}-{conn.hub1.name}-{conn.hub2.name}")
                    continue
                if drone.plan_index + 1 < len(drone.plan):
                    next_hub = drone.plan[drone.plan_index + 1]
                    conn = next(
                        c for c in drone.position.connections if next_hub in (c.hub1, c.hub2))
                    key = "-".join(sorted([conn.hub1.name, conn.hub2.name]))
                    if next_hub.zone_type == "restricted":
                        occupants = sum(
                            1 for drone in self.drones if drone.position == next_hub)
                        on_link = sum(
                            1 for drone in self.drones if drone.position is conn)
                        reserved = sum(
                            1 for drone in self.drones if drone.destination == next_hub)
                        if (on_link + link_usage.get(key, 0) + 1 <= conn.max_link_capacity
                                and occupants + reserved + 1 <= next_hub.max_drones or next_hub.is_end):
                            drone.remaining_turns = 2
                            drone.destination = next_hub
                            drone.position = conn
                            drone.plan_index += 1
                            link_usage[key] = link_usage.get(key, 0) + 1
                            moves.append(
                                f"D{drone.id}-{conn.hub1.name}-{conn.hub2.name}")
                        else:
                            continue
                    else:
                        occupants = sum(
                            1 for drone in self.drones if drone.position == next_hub)
                        on_link = sum(
                            1 for drone in self.drones if drone.position is conn)
                        if on_link + link_usage.get(key, 0) + 1 <= conn.max_link_capacity and (occupants + 1 <= next_hub.max_drones or next_hub.is_end):
                            drone.position = next_hub
                            drone.plan_index += 1
                            link_usage[key] = link_usage.get(key, 0) + 1
                            if drone.position == self.end:
                                drone.is_delivered = True
                            moves.append(f"D{drone.id}-{drone.position.name}")
                else:
                    continue
            trace.append(" ".join(moves))
        return trace
