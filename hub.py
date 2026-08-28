#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   hub.py                                               :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: nda-roch <nda-roch@student.42porto.com>      +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/08/28 11:52:39 by nda-roch            #+#    #+#            #
#   Updated: 2026/08/28 12:15:22 by nda-roch           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

from dataclasses import dataclass, field


@dataclass
class Hub:
    name: str
    x: int
    y: int
    zone_type: str              # "normal", "restricted", "priority", "blocked"
    max_drones: int = 1         # default 1, max 2, start/end unlimited
    current_occupants: int = 0
    color: str | None = None
    connections: list[Connection] = field(default_factory=list)
    is_start: bool = False
    is_end: bool = False
