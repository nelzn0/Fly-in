#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   exceptions.py                                        :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: nda-roch <nda-roch@student.42porto.com>      +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 15:34:52 by nda-roch            #+#    #+#            #
#   Updated: 2026/09/08 15:43:26 by nda-roch           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

class FlyInError(Exception):
    def __init__(self, line_n: int | None, message: str) -> None:
        self.line_n = line_n
        self.message = message
        if line_n is None:
            text = message
        else:
            text = f"Line {line_n}: {message}"
        super().__init__(text)


class ParseError(FlyInError):
    pass


class SimulationError(FlyInError):
    pass
