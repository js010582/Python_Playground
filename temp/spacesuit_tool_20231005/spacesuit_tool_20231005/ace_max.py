#!/usr/bin/env python3

"""SPACE protocol definitions for the ACE Max thruster.

Imports brings in all of the ACE common definitions, so this file is only
the additional specific differences for ACE Max.

The canonical reference for the commands is this design doc:
    https://docs.google.com/document/d/1ubxcPF__EAEKWYdPicY2YRF4y8Y2wsH61LEIfDUPw0E
"""

__copyright__ = "Copyright 2020, Apollo Fusion Inc."

import space
from ace_common import CMD, COMMANDS


# Parameter identifiers
MAGCOIL = space.IdentifierParser()
MAGCOIL.add(0, 'inner', aliases=('in', '0'))
MAGCOIL.add(1, 'outer', aliases=('out', '1'))


# List of commands to be registered
COMMANDS += [
  # Operational commands
  CMD(0x14, 'magcoil', 0.005,
      space.ListParser(space.PairParser(MAGCOIL, space.FloatParser())),
      space.ListParser(space.PairParser(MAGCOIL, space.FloatParser()))),
  ]


if __name__ == '__main__':
  print("This library isn't intended to be run directly.")
