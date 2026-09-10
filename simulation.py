#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   simulation.py                                        :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: nda-roch <nda-roch@student.42porto.com>      +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/10 14:56:44 by nda-roch            #+#    #+#            #
#   Updated: 2026/09/10 16:37:55 by nda-roch           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

from parser import ParsedMap
from drone import Drone
from models import Hub
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

    def run(self) -> None:
        while not all(drone.is_delivered for drone in self.drones):
            moves = []
            for drone in self.drones:
                if drone.plan_index + 1 < len(drone.plan):
                    next_hub = drone.plan[drone.plan_index + 1]
                    drone.position = next_hub
                    drone.plan_index += 1
                if drone.position == self.end:
                    drone.is_delivered = True
                moves.append(f"D{drone.id}-{drone.position.name}")
            print(" ".join(moves))
