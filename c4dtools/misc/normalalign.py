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
c4dtools.misc.normalalign
~~~~~~~~~~~~~~~~~~~~~~~~~

New in 1.2.5.

This module implements a function for checking the alignment of the
normals of a polygon-object.
"""

import c4d
import math

from c4d.utils import GeRayCollider, VectorAngle
from c4dtools.utils import assert_type, PolygonObjectInfo
from operator import xor

def test_object_normals(op, info=None, logger=None):
    r"""
    Tests the polygon-object *op*'s normals if they're pointing to the
    in or outside of the object. Returns a list of boolean variables
    where each index defines wether the associated polygon's normal
    is pointing into the right direction or not.

    The algorithm works best on completely closed shapes with one
    segment only. The polygon-object should also be valid, therefore not
    more than two polygons per edge, etc. The results might be incorrect
    with an invalid mesh structure.

    :param op: A :class:`c4d.PolygonObject` instance to test.
    :param info: A :class:`~c4dtools.utils.PolygonObjectInfo` instance for
            the passed object, or None to generate on demand.
    :return:   :class:`list` of `bool` and the PolygonObjectInfo
            instance.
    """

    if not info:
        info = PolygonObjectInfo()
        info.init(op)
    if info.polycount <= 0:
        return ([], None)

    collider = GeRayCollider()
    if not collider.Init(op):
        raise RuntimeError('GeRayCollider could not be initialized.')

    mg = op.GetMg()
    mp = op.GetMp()
    size = op.GetRad()

    # Define three camera position for the object. We could simply use
    # one if there wouldn't be the special case where a polygon's normal
    # is exactly in an angle of 90°, where we can not define wether the
    # normal is correctly aligned or not.

    maxp = mp + size + c4d.Vector(size.GetLength() * 2)
    cam1 = c4d.Vector(maxp.x, 0, 0)
    cam2 = c4d.Vector(0, maxp.y, 0)
    cam3 = c4d.Vector(0, 0, maxp.z)

    # Check each polygon from each camera position for the angle between
    # them. If one of the angles is greater than 90°, the face is pointing
    # into the wrong direction.

    result = []
    iterator = enumerate(zip(info.normals, info.midpoints))
    for index, (normal, midpoint) in iterator:
        normal_aligned = False

        for cam in [cam1, cam2, cam3]:

            # Compute the direction vector from the cam to the midpoint
            # of the polygon and the ray length to garuantee a hit with
            # the polygon.
            direction = (midpoint - cam)
            length = direction.GetLengthSquared()
            direction.Normalize()

            # Compute the intersections point from the cam to the midpoint
            # of the polygon.
            collider.Intersect(cam, direction, length)
            intersections = {}
            for i in xrange(collider.GetIntersectionCount()):
                isect = collider.GetIntersection(i)

                # The GeRayCollider class may yield doubled intersections,
                # we filter them out this way.
                if isect['face_id'] not in intersections:
                    intersections[isect['face_id']] = isect

            # Sort the intersections by distance to the cam.
            intersections = sorted(
                    intersections.values(),
                    key=lambda x: x['distance'])

            # Find the intersection with the current polygon and how
            # many polygons have been intersected before this polygon
            # was intersection.
            isect_index = -1
            isect = None
            for i, isect in enumerate(intersections):
                if isect['face_id'] == index:
                    isect_index = i
                    break

            # We actually *have* to find an intersection, it would be
            # a strange error if we wouldn't have found one.
            if isect_index < 0:
                if logger:
                    message = "No intersection with face %d from cam %s"
                    logger.warning(message % (index, cam))
                continue

            angle = VectorAngle(normal, direction * -1)

            # If there has been one intersection with another face before
            # the intersection with the current polygon, the polygon is
            # assumed to be intended to face away from the camera. Same for
            # all other odd numbers of intersection that have occured
            # before the intersection with the current face.
            if isect_index % 2:
                angle = (math.pi / 2) - angle

            if not xor(isect['backface'], isect_index % 2):
                normal_aligned = True

        result.append(normal_aligned)

    return result, info

def align_object_normals(op, info=None, logger=None):
    r"""
    Align the passed polygon-object's normals to point to the outside of
    the object. The same algorithmic restrictions as for
    :func:`test_object_normals` apply. The parameters do also equal.
    """

    nstate, info = test_object_normals(op, info, logger)
    for i, state in enumerate(nstate):
        if not state:
            p = info.polygons[i]
            if p.c == p.d:
                p.a, p.b, p.c = p.c, p.b, p.a
                p.d = p.c
            else:
                p.a, p.b, p.c, p.d = p.d, p.c, p.b, p.a

            op.SetPolygon(i, p)

    op.Message(c4d.MSG_CHANGE)


