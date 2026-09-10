#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   pathfinder.py                                        :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: nda-roch <nda-roch@student.42porto.com>      +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 17:14:26 by nda-roch            #+#    #+#            #
#   Updated: 2026/09/10 15:45:46 by nda-roch           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

from models import Hub


def find_path(start: Hub, end: Hub, hubs: dict[str, Hub], load: dict[str, float]) -> list[Hub]:

    costs = {hub.name: float('inf') for hub in hubs.values()}
    costs[start.name] = 0

    came_from = {hub.name: None for hub in hubs.values()}

    frontier = [start.name]

    settled = set()

    while frontier:
        current = min(frontier, key=lambda name: costs[name])
        frontier.remove(current)
        settled.add(current)

        if current == end.name:
            break

        for connection in hubs[current].connections:
            if hubs[current] is connection.hub1:
                neighbor = connection.hub2
            else:
                neighbor = connection.hub1

            if neighbor.name in settled:
                continue

            if neighbor.zone_type == "blocked":
                continue

            if neighbor.zone_type == "restricted":
                move_cost = 2
            else:
                move_cost = 1

            new_cost = costs[current] + move_cost + \
                load.get(neighbor.name, 0.0)

            if new_cost < costs[neighbor.name]:
                costs[neighbor.name] = new_cost
                came_from[neighbor.name] = current
                frontier.append(neighbor.name)

    current = end.name
    path = []

    while current:
        path.append(hubs[current])
        current = came_from[current]

    path.reverse()
    return path
