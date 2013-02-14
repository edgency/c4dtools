# Copyright (c) 2012-2013, Niklas Rosenstein
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met: 
# 
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer. 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution. 
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# 
# The views and conclusions contained in the software and
# documentation are those of the authors and should not be interpreted
# as representing official policies,  either expressed or implied, of
# the FreeBSD Project.
r"""
c4dtools.misc.boundingbox
~~~~~~~~~~~~~~~~~~~~~~~~~

Utility for computing the bounding-box spanned by a couple of vectors
or by :class:`c4d.BaseObject` instances.
"""

import c4d
import copy
from c4dtools.utils import clsname, vmin, vmax

class AABB(object):
    r"""
    This class makes it easy to compute the bounding-box of a set of
    points or even objects. AABB is short for "axis-aligned bounding-box".

    Example for Script Manager:

    .. code-block:: python

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

    .. code-block:: python

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
        Expand the bounding-box by the passed :class:`c4d.BaseObject`
        instance. The method can optionally continue recursively.

        Raises: TypeError when *obj* is not an instance of
                :class:`c4d.BaseObject`.
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


