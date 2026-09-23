#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   renderer.py                                          :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: nda-roch <nda-roch@student.42porto.com>      +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/18 17:32:51 by nda-roch            #+#    #+#            #
#   Updated: 2026/09/23 19:25:38 by nda-roch           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

from parser import ParsedMap
import pygame


def run_renderer(parsed: ParsedMap, trace: list[str]):
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080))
    clock = pygame.time.Clock()
    running = True

    turn_index = 0
    last_advance = pygame.time.get_ticks()
    BEAT_MS = 700
    font = pygame.font.SysFont("arial", 15)
    CELL_SIZE = 70
    MARGIN = 50

    xs = [hub.x for hub in parsed.hubs.values()]
    ys = [hub.y for hub in parsed.hubs.values()]

    min_x = min(xs)
    min_y = min(ys)

    occupancy = {}

    while running:
        screen.fill("purple")
        for hub in parsed.hubs.values():
            px = (hub.x - min_x) * CELL_SIZE + MARGIN
            py = (hub.y - min_y) * CELL_SIZE + MARGIN
            pygame.draw.circle(screen, hub.color or "white", (px, py), 25)
            hub_surface = font.render(hub.name, True, "white")
            screen.blit(hub_surface, (px + 30, py - 58))
            hub_type = font.render(hub.zone_type, True, "white")
            screen.blit(hub_type, (px + 30, py - 40))
        for connection in parsed.connections:
            a = parsed.hubs[connection.hub1.name]
            b = parsed.hubs[connection.hub2.name]
            ax = (a.x - min_x) * CELL_SIZE + MARGIN
            ay = (a.y - min_y) * CELL_SIZE + MARGIN
            bx = (b.x - min_x) * CELL_SIZE + MARGIN
            by = (b.y - min_y) * CELL_SIZE + MARGIN
            pygame.draw.line(screen, "blue", (ax, ay), (bx, by), 3)
        palette = ["green", "blue", "yellow", "orange"]
        for move in trace[turn_index].split():
            drone_id, location = move.split("-", 1)
            if location in parsed.hubs:
                hub = parsed.hubs[location]
                px = (hub.x - min_x) * CELL_SIZE + MARGIN
                py = (hub.y - min_y) * CELL_SIZE + MARGIN
            else:
                loc_h1, loc_h2 = location.split("-", 1)
                loc_key = "-".join(sorted([loc_h1, loc_h2]))
                conn = next(c for c in parsed.connections if loc_key ==
                            "-".join(sorted([c.hub1.name, c.hub2.name])))
                ax = (conn.hub1.x - min_x) * CELL_SIZE + MARGIN
                ay = (conn.hub1.y - min_y) * CELL_SIZE + MARGIN
                bx = (conn.hub2.x - min_x) * CELL_SIZE + MARGIN
                by = (conn.hub2.y - min_y) * CELL_SIZE + MARGIN
                px, py = (ax + bx) // 2, (ay + by) // 2
            color = palette[int(drone_id[1:]) % len(palette)]
            pygame.draw.circle(screen, color, (px, py), 12)
            drone_surface = font.render(drone_id, True, "white")
            screen.blit(drone_surface, (px + 30, py - 18))
        text_surface = font.render(f"Turn {turn_index}", True, "white")
        screen.blit(text_surface, (10, 10))
        pygame.display.flip()
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        if turn_index < len(trace) - 1:
            time_now = pygame.time.get_ticks()
            if time_now - last_advance >= BEAT_MS:
                turn_index += 1
                last_advance = time_now

    pygame.quit()
