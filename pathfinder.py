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

"""Finds the cheapest path for a drone from the start to the end zone."""

from models import Hub
from exceptions import SimulationError

# how many turns it costs to step into each zone type
RESTRICTED_COST = 2
# priority is 0.5 here so the pathfinder likes these zones more.
# the real move still takes 1 turn in the simulation.
PRIORITY_COST = 0.5
NORMAL_COST = 1


class Pathfinder:
    """Finds paths with a Dijkstra-style search.

    It works like Dijkstra's algorithm, written by hand with a plain list.
    Each step settles the cheapest zone that is not settled yet. The cost of
    a zone is its zone type cost plus the load on it, so zones that other
    drones already use look more expensive.

    Attributes:
        hubs: All the zones on the map, by name.
        start: The start zone.
        end: The end zone.
    """

    def __init__(self, hubs: dict[str, Hub], start: Hub, end: Hub) -> None:
        """Stores the map so the search can use it.

        Args:
            hubs: All the zones on the map, by name.
            start: The start zone.
            end: The end zone.
        """
        self.hubs = hubs
        self.start = start
        self.end = end

    def _move_cost(self, hub: Hub) -> float:
        """Gets how expensive it is to step into a zone.

        Blocked zones are skipped before this is called, so they never get
        here.

        Args:
            hub: The zone we want to step into.

        Returns:
            The cost of the zone type.
        """
        if hub.zone_type == "restricted":
            return RESTRICTED_COST
        elif hub.zone_type == "priority":
            return PRIORITY_COST
        else:
            return NORMAL_COST

    def _neighbors(self, hub: Hub) -> list[Hub]:
        """Lists the zones that are connected to this one.

        Args:
            hub: The zone to check.

        Returns:
            The zone on the other side of each connection.
        """
        neighbors = []
        for connection in hub.connections:
            # a connection has two ends, so we take the one we are not on
            if hub is connection.hub1:
                neighbors.append(connection.hub2)
            else:
                neighbors.append(connection.hub1)
        return neighbors

    def find_path(self, load: dict[str, float]) -> list[Hub]:
        """Finds the cheapest path from the start zone to the end zone.

        Args:
            load: Extra cost per zone name, from the drones that are already
                planned. Zones that are not in this dict have no extra cost.

        Returns:
            The zones in order, from the start to the end (both included).

        Raises:
            SimulationError: If the end zone can't be reached.
        """
        # every zone starts at infinity, except the start, which costs 0
        costs = {hub.name: float('inf') for hub in self.hubs.values()}
        costs[self.start.name] = 0

        # the zone each zone was reached from, to rebuild the path at the end
        came_from: dict[str, str | None] = {
            hub.name: None for hub in self.hubs.values()
        }

        # zones we found but have not settled yet
        frontier = [self.start.name]

        # zones whose cheapest cost is final
        settled = set()

        while frontier:
            # take the cheapest zone we know about
            current: str = min(frontier, key=lambda name: costs[name])
            frontier.remove(current)
            settled.add(current)

            # the end is settled, so we already have the cheapest path to it
            if current == self.end.name:
                break

            for neighbor in self._neighbors(self.hubs[current]):

                # a settled zone can't get a cheaper cost anymore
                if neighbor.name in settled:
                    continue

                if neighbor.zone_type == "blocked":
                    continue

                move_cost = self._move_cost(neighbor)

                # stepping in costs the zone type plus the load on the zone
                new_cost = costs[current] + move_cost + \
                    load.get(neighbor.name, 0.0)

                if new_cost < costs[neighbor.name]:
                    costs[neighbor.name] = new_cost
                    came_from[neighbor.name] = current
                    # the same zone can be added more than once,
                    # the settled check above skips the extra copies
                    frontier.append(neighbor.name)

        if self.end.name not in settled:
            raise SimulationError(None, "End is unreachable")

        # walk back from the end to the start, then flip the list
        step_back: str | None = self.end.name
        path = []

        while step_back:
            path.append(self.hubs[step_back])
            step_back = came_from[step_back]

        path.reverse()
        return path
