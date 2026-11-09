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

"""Entry point of Fly-in. Run it with a map file to start the simulation."""

from parser import Parser
from exceptions import FlyInError
from sys import argv, exit
from simulation import Simulation


def main() -> None:
    """Runs the program from start to finish.

    Reads the map file from the command line, parses it, plans the paths
    and runs the simulation. Then it asks if you want the terminal output
    or the graphical view.

    Raises:
        SystemExit: If the arguments are wrong or the map can't be used.
    """
    # the program needs exactly one thing: the map file
    if len(argv) != 2:
        print("Error: Usage: python main.py <map_file>")
        exit(1)
    try:
        parsed_map = Parser().parse(argv[1])
        sim = Simulation(parsed_map)
        sim.drone_paths()
        trace = sim.run()

    # a bad map, a missing file or a stuck simulation all stop here
    except (FlyInError, FileNotFoundError) as e:
        print(f"Error: {e}")
        exit(1)

    # the trace is already done, so the user only picks how to see it
    choice = input("1 - Terminal / 2 - Graphical Interface\n")

    if choice == "2":
        # importing renderer also imports pygame, so it only happens here
        from renderer import Renderer
        renderer = Renderer(parsed_map, trace)
        renderer.run()
    else:
        from terminaloutput import TerminalOutput
        toutput = TerminalOutput(trace)
        toutput.show()


if __name__ == "__main__":
    main()
