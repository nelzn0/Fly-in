#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   pathfinder.py                                        :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: nda-roch <nda-roch@student.42porto.com>      +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 17:14:26 by nda-roch            #+#    #+#            #
#   Updated: 2026/09/23 19:28:18 by nda-roch           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

from models import Hub
from exceptions import SimulationError

RESTRICTED_COST = 2
PRIORITY_COST = 0.5
NORMAL_COST = 1


class Pathfinder:
    def __init__(self, hubs: dict[str, Hub], start: Hub, end: Hub) -> None:
        self.hubs = hubs
        self.start = start
        self.end = end

    def _move_cost(self, hub: Hub) -> float:
        if hub.zone_type == "restricted":
            return RESTRICTED_COST
        elif hub.zone_type == "priority":
            return PRIORITY_COST
        else:
            return NORMAL_COST

    def _neighbors(self, hub: Hub) -> list[Hub]:
        neighbors = []
        for connection in hub.connections:
            if hub is connection.hub1:
                neighbors.append(connection.hub2)
            else:
                neighbors.append(connection.hub1)
        return neighbors

    def find_path(self, load: dict[str, float]) -> list[Hub]:

        costs = {hub.name: float('inf') for hub in self.hubs.values()}
        costs[self.start.name] = 0

        came_from = {hub.name: None for hub in self.hubs.values()}

        frontier = [self.start.name]

        settled = set()

        while frontier:
            current = min(frontier, key=lambda name: costs[name])
            frontier.remove(current)
            settled.add(current)

            if current == self.end.name:
                break

            for neighbor in self._neighbors(self.hubs[current]):

                if neighbor.name in settled:
                    continue

                if neighbor.zone_type == "blocked":
                    continue

                move_cost = self._move_cost(neighbor)

                new_cost = costs[current] + move_cost + \
                    load.get(neighbor.name, 0.0)

                if new_cost < costs[neighbor.name]:
                    costs[neighbor.name] = new_cost
                    came_from[neighbor.name] = current
                    frontier.append(neighbor.name)

        if self.end.name not in settled:
            raise SimulationError(None, "End is unreachable")

        current = self.end.name
        path = []

        while current:
            path.append(self.hubs[current])
            current = came_from[current]

        path.reverse()
        return path
