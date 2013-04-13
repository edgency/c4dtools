# coding: utf-8
#
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
from c4dtools.utils import vmin, vmax, ensure_type

class AABB(object):
    r"""
    Expandable bounding-box system.

    *Changed in 1.2.9*: Re-implementation, interface has changed.

    - ``expand()`` is now called ``expand_object()``
    - ``expand_point()`` is now called ``expand()``
    - ``translation_matrix`` is not called ``translation``
    - Initialization is done with the first call to :meth:`expand`
    - Polygon objects are now treated in a special way
    """

    def __init__(self, translation=None):
        super(AABB, self).__init__()
        if translation is None:
            translation = c4d.Matrix()

        self.minv = None
        self.maxv = None
        self.init = False
        self.translation = translation

    def expand(self, point):
        point = point * self.translation
        if not self.init:
            self.minv = c4d.Vector(point)
            self.maxv = c4d.Vector(point)
            self.init = True
        else:
            self.minv = vmin(self.minv, point)
            self.maxv = vmax(self.maxv, point)

    def expand_object(self, obj, recursive=False):
        ensure_type(obj, c4d.BaseObject)
        mg = obj.GetMg()
        
        if isinstance(obj, c4d.PointObject):
            for p in obj.GetAllPoints():
                self.expand(p * mg)
        else:
            mp = obj.GetMp()
            bb = obj.GetRad()
    
            V = c4d.Vector
    
            self.expand(V(mp.x + bb.x, mp.y + bb.y, mp.z + bb.z) * mg)
            self.expand(V(mp.x - bb.x, mp.y + bb.y, mp.z + bb.z) * mg)
            self.expand(V(mp.x + bb.x, mp.y + bb.y, mp.z - bb.z) * mg)
            self.expand(V(mp.x - bb.x, mp.y + bb.y, mp.z - bb.z) * mg)
    
            self.expand(V(mp.x + bb.x, mp.y - bb.y, mp.z + bb.z) * mg)
            self.expand(V(mp.x - bb.x, mp.y - bb.y, mp.z + bb.z) * mg)
            self.expand(V(mp.x + bb.x, mp.y - bb.y, mp.z - bb.z) * mg)
            self.expand(V(mp.x - bb.x, mp.y - bb.y, mp.z - bb.z) * mg)

        if recursive:
            for child in obj.GetChildren():
                self.expand_object(child, True)

    @property
    def midpoint(self):
        return (self.minv + self.maxv) * 0.5

    @property
    def size(self):
        return (self.maxv - self.minv) * 0.5




