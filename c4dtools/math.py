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
c4dtools.math
~~~~~~~~~~~~~

*New in 1.3.0*. This module contains helpers for mathematical operations.
"""

import c4d
import collections

from c4d import Vector
from c4dtools.utils import ensure_type

PRECISION = 0.000001

def vmin(a, b):
    r"""
    Combines the lowest components of the two vectors *a* and *b* into
    a new vector. Returns the new vector.

    *Changed in 1.3.0*:

        - The new vector is now returned instead of stored in *a*.
        - Moved to :mod:`c4dtools.math`.
    """

    c = Vector(a)
    if b.x < a.x: c.x = b.x
    if b.y < a.y: c.y = b.y
    if b.z < a.z: c.z = b.z
    return c

def vmax(a, b):
    r"""
    Combines the highest components of the two vectors *a* and *b* into
    a new vector. Returns the new vector.

    *Changed in 1.3.0*:

        - The new vector is now returned instead of stored in *a*.
        - Moved to :mod:`c4dtools.math`.
    """

    c = Vector(a)
    if b.x > a.x: c.x = b.x
    if b.y > a.y: c.y = b.y
    if b.z > a.z: c.z = b.z
    return c

def vbbmid(vectors):
    r"""
    Returns the mid-point of the bounding box spanned by the list
    of vectors. This is different to the arithmetic middle of the
    points.

    *Changed in 1.3.0*:

        - Moved to :mod:`c4dtools.math`.
        - Raises *ValueError* if *vectors* is not a sequence type
          or is empty.

    Returns: :class:`c4d.Vector`
    """

    ensure_type(vectors, collections.Sequence, name='vectors')
    vectors = tuple(vectors)
    if not vectors:
        raise ValueError('An empty sequence is not accepted.')

    min = Vector(vectors[0])
    max = Vector(min)
    for v in vectors:
        vmin(min, v)
        vmax(max, v)

    return (min + max) * 0.5

class Line(object):
    r"""
    *New in 1.3.0*.

    This class represents a parametrical representation of a line in 3
    dimensional space.

    .. attribute:: p

        A :class:`c4d.Vector` being an element of the line.

    .. attribute:: d

        The direction vector of the line. It is **not** necessarily
        normalized.
    """

    @classmethod
    def from_2(self, p1, p2):
        r"""
        *New in 1.3.0*.

        Creates a :class:`Line` object from two points in three dimensional 
        space.

        :param p1: The first point of the line (:class:`c4d.Vector`)
        :param p2: The second point of the line (:class:`c4d.Vector`)
        """

        return Line(p1, (p2 - p1))

    def __init__(self, p, d):
        r"""
        *New in 1.3.0*.

        Initialize the line with one point on the line and its direction
        vector. Both, *p* and *d* may be iterables. In this case, they must
        be iterables with one to three elements because they will be extracted
        to the :class:`c4d.Vector` constructor.

        The direction vector is normalized. The vectors are copied internally.

        :param p: An element of the line (:class:`c4d.Vector`)
        :param d: The direction vector of the line (:class:`c4d.Vector`)
        """

        if isinstance(p, collections.Sequence):
            p = Vector(*p)
        if isinstance(d, collections.Sequence):
            d = Vector(*d)

        ensure_type(p, Vector, name='p')
        ensure_type(d, Vector, name='d')

        self.p = Vector(p)
        self.d = d.GetNormalized()

    def __repr__(self):
        return 'Line(p:[%s], d:[%s])' % (self.p, self.d)

    def eval(self, a):
        r"""
        *New in 1.3.0*.

        Returns a :class:`c4d.Vector` resulting in solving the parametrical
        equation of the line using the parameter *a*.
        """

        return self.p + self.d * a

    def intersection(self, line, precision=PRECISION):
        r"""
        *New in 1.3.0*.

        Calculates the intersection point of the calling and the passed
        *line*.

        :param line: The complementary line to check for intersection with
                the calling line.
        :param precision: The allowed deviation between the components of
                the linear factors.
        :return: :class:`c4d.Vector` if the lines intersect, ``None`` if
                they do not.

        .. seealso:: :func:`line_intersection`
        """

        ensure_type(line, Line, name='line')
        return line_intersection(self.p, self.d, line.p, line.d, precision)

def line_intersection(p1, d1, p2, d2, precision=PRECISION):
    r"""
    *New in 1.3.0*.

    Calculates the intersection point of two lines defined by *p1*,
    *d1*, *p2* and *d2*.

    :param p1: A point on the first line (:class:`c4d.Vector`)
    :param d1: The direction of the first line  (:class:`c4d.Vector`)
    :param p2: A point on the second line  (:class:`c4d.Vector`)
    :param d2: The direction of the second line  (:class:`c4d.Vector`)
    :param precision: The allowed deviation between the components of
            the linear factors.
    :return: :class:`c4d.Vector` if the lines intersect, ``None`` if they
            do not.
    """

    a = d1.Cross(d2)
    b = (p2 - p1).Cross(d2)
    c = Vector(b.x / a.x, b.y / a.y, b.z / a.z)

    # Now check if the resulting deviation can be accepted.
    ref = c.x
    val = ref
    for v in (c.y, c.z):
        if abs(v - ref) > precision:
            return None
        val += v

    return p1 + d1 * val / 3.0





