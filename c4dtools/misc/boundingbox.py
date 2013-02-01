# coding: utf-8
#
# Copyright (C) 2012, Niklas Rosenstein
# Licensed under the GNU General Public License

import c4d
import copy
from c4dtools.utils import clsname, vmin, vmax

class AABB(object):
    r"""
    This class makes it easy to compute the bounding-box of a set of
    points or even objects. AABB is short for "axis-aligned bounding-box".

    Example for Script Manager:

        from c4dtools.misc.boundingbox import AABB
        box = AABB()
        box.expand(op, recursive=True)
        print box.midpoint
        print box.size

    The bounding box is *always* calculated from global coordinates and
    is translated with the matrix in the translation_matrix slot. The
    translation can not be performed after expansion of the bounding-
    box, the translation_matrix must therefore be set *before*
    expand() or expand_point() is called.

        from c4dtools.misc.boundingbox import AABB
        box = AABB(translation_matrix=~op.GetMg())
        box.expand(mg, recursive=True)
        print box.midpoint
        print box.size
    """

    def __init__(self, min_v=c4d.Vector(0), max_v=c4d.Vector(0),
                 translation_matrix=c4d.Matrix()):
        super(AABB, self).__init__()
        self.min_v = copy.copy(min_v)
        self.max_v = copy.copy(max_v)
        self.translation_matrix = copy.copy(translation_matrix)

    def expand(self, obj, recursive=False):
        r"""
        Expand the bounding-box by the passed c4d.BaseObject instance.
        The method can optionally continue recursively.

        Raises: TypeError when *obj* is not an instance of
                c4d.BaseObject.
        """

        if not isinstance(obj, c4d.BaseObject):
            raise TypeError('expected c4d.BaseObject, got %s.' % clsname(obj))

        matrix = obj.GetMg()
        mp = obj.GetMp()
        bb = obj.GetRad()

        v = c4d.Vector

        self.expand_point(v(mp.x + bb.x, mp.y + bb.y, mp.z + bb.z) * matrix)
        self.expand_point(v(mp.x - bb.x, mp.y + bb.y, mp.z + bb.z) * matrix)
        self.expand_point(v(mp.x + bb.x, mp.y + bb.y, mp.z - bb.z) * matrix)
        self.expand_point(v(mp.x - bb.x, mp.y + bb.y, mp.z - bb.z) * matrix)

        self.expand_point(v(mp.x + bb.x, mp.y - bb.y, mp.z + bb.z) * matrix)
        self.expand_point(v(mp.x - bb.x, mp.y - bb.y, mp.z + bb.z) * matrix)
        self.expand_point(v(mp.x + bb.x, mp.y - bb.y, mp.z - bb.z) * matrix)
        self.expand_point(v(mp.x - bb.x, mp.y - bb.y, mp.z - bb.z) * matrix)

        if recursive:
            for child in obj.GetChildren():
                self.expand(child, True)

    def expand_point(self, point):
        r"""
        Expand the bounding-box by the passed c4d.Vector representing
        a point in the 3-dimensional space.

        Raises: TypeError when *point* is not an instance of
                c4d.Vector.
        """

        vmin(self.min_v, point * self.translation_matrix)
        vmax(self.max_v, point * self.translation_matrix)

    @property
    def midpoint(self):
        r"""
        Calcuates and returns the midpoint of the bounding-box yet
        created.
        """

        return (self.min_v + self.max_v) * 0.5

    @property
    def size(self):
        r"""
        Returns the size of the bounding-box yet created. The size
        plus the midpoint of the bounding-box is the upper-right-front
        corner of the box.
        """

        return (self.max_v - self.min_v) * 0.5
