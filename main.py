#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   main.py                                              :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: nda-roch <nda-roch@student.42porto.com>      +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/08/27 14:38:52 by nda-roch            #+#    #+#            #
#   Updated: 2026/09/23 19:32:57 by nda-roch           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

from parser import Parser
from exceptions import FlyInError
from sys import argv, exit
from simulation import Simulation
from renderer import run_renderer


def main() -> None:
    try:
        parsed_map = Parser().parse(argv[1])
        sim = Simulation(parsed_map)
        sim.drone_paths()
        trace = sim.run()

    except FlyInError as e:
        print(f"Error: {e}")
        exit(1)

    choice = input("1 - Terminal / 2 - Graphical Interface")
    if choice == "2":
        run_renderer(parsed_map, trace)
    else:
        n = 1
        for line in trace:
            print(f"Turn {n}:")
            print()
            print(line.replace(' ', '\n'))
            print()
            n += 1


if __name__ == "__main__":
    main()
