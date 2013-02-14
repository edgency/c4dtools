#
# Fake module.
#

from . import modules
from . import plugins

class BaseContainer:
    pass

class Vector:

    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return 'Vector(%.3f, %.3f, %.3f)' % (self.x, self.y, self.z)

class Matrix:

    def __init__(self, v1=Vector(), v2=Vector(), v3=Vector(), off=Vector()):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3
        self.off = off

    def __repr__(self):
        return 'Matrix(v1: %s, v2: %s, v3: %s, off: %s)' % (
            self.v1, self.v2, self.v3, self.off)

PLUGINFLAG_COMMAND_HOTKEY = 0

