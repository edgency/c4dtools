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

def vmin(a, b):
    r"""
    Combines the lowest components of the two vectors *a* and *b* into
    a new vector. Returns the new vector.

    *Changed in 1.3.0*:

        - The new vector is now returned instead of stored in *a*.
        - Moved to :mod:`c4dtools.math`.
    """

    c = c4d.Vector(a)
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

    c = c4d.Vector(a)
    if b.x > a.x: c.x = b.x
    if b.y > a.y: c.y = b.y
    if b.z > a.z: c.z = b.z
    return c

def vbbmid(vectors):
    r"""
    Returns the mid-point of the bounding box spanned by the list
    of vectors. This is different to the arithmetic middle of the
    points.

    *Changed in 1.3.0.0*: Moved to :mod:`c4dtools.math`.

    Returns: :class:`c4d.Vector`
    """

    if not vectors:
        return c4d.Vector(0)

    min = c4d.Vector(vectors[0])
    max = c4d.Vector(min)
    for v in vectors:
        vmin(min, v)
        vmax(max, v)

    return (min + max) * 0.5



