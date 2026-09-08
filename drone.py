#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   drone.py                                             :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: nda-roch <nda-roch@student.42porto.com>      +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 15:23:33 by nda-roch            #+#    #+#            #
#   Updated: 2026/09/08 15:34:07 by nda-roch           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

from dataclasses import dataclass
from models import Hub, Connection


@dataclass
class Drone:
    id: int
    position: Hub | Connection
    destination: Hub | None
    remaining_turns: int = 0
    is_delivered: bool = False
