#
# Fake module.
#

from . import modules
from . import plugins

class BaseContainer:
    pass

class Vector:

    def __init__(self, *args):
        pass

    def __repr__(self):
        return 'Vector()'

class Matrix:

    def __init__(self, v1=Vector(), v2=Vector(), v3=Vector(), off=Vector()):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3
        self.off = off

    def __repr__(self):
        return 'Matrix()'

PLUGINFLAG_COMMAND_HOTKEY = 0

