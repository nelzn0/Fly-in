#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   models.py                                            :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: nda-roch <nda-roch@student.42porto.com>      +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 13:52:35 by nda-roch            #+#    #+#            #
#   Updated: 2026/09/08 14:49:37 by nda-roch           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

from __future__ import annotations
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


@dataclass
class Connection:
    hub1: Hub
    hub2: Hub
    max_link_capacity: int = 1
    current_occupants: int = 0
