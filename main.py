#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   main.py                                              :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: nda-roch <nda-roch@student.42porto.com>      +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/08/27 14:38:52 by nda-roch            #+#    #+#            #
#   Updated: 2026/09/08 16:42:29 by nda-roch           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

from parser import Parser
from exceptions import FlyInError
from sys import argv, exit


def main() -> None:
    try:
        parsed_map = Parser().parse(argv[1])

    except FlyInError as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
