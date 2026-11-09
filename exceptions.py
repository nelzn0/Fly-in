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

"""The errors used across the project."""


class FlyInError(Exception):
    """The base error of the project.

    It adds the line number to the message when there is one.
    """

    def __init__(self, line_n: int | None, message: str) -> None:
        """Builds the error text.

        Args:
            line_n: The line of the map file where the error is, or None
                if the error is not about one line.
            message: What went wrong.
        """
        self.line_n = line_n
        self.message = message
        # only add "Line N:" when we know the line
        if line_n is None:
            text = message
        else:
            text = f"Line {line_n}: {message}"
        super().__init__(text)


class ParseError(FlyInError):
    """Raised when the map file has a wrong line, field or value."""


class SimulationError(FlyInError):
    """Raised when the simulation can't go on, like an unreachable end."""
