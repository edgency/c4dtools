# coding: utf-8
#
# Copyright (C) 2012, Niklas Rosenstein

import os
import c4d

def change_suffix(filename, new_suffix):
    r"""
    Replaces the suffix of the passed filename with *new_suffix*.
    """

    index = filename.rfind('.')
    if index >= 0:
        filename = filename[:index]

    return '%s.%s' % (filename, new_suffix)

def file_changed(original, copy):
    r"""
    Returns True when the filename pointed by *original* was modified
    before the last time *copy* was modified, False otherwise.
    """

    return os.path.getmtime(original) > os.path.getmtime(copy)

def vmin(dest, test):
    r"""
    For each component of the vectors *dest* and *test*, write the
    lower value of each pairs into the respective component of *dest*.
    """

    if test.x < dest.x: dest.x = test.x
    if test.y < dest.y: dest.y = test.y
    if test.z < dest.z: dest.z = test.z

def vmax(dest, test):
    r"""
    For each component of the vectors *dest* and *test*, write the
    upper value of each pairs into the respective component of *dest*.
    """

    if test.x > dest.x: dest.x = test.x
    if test.y > dest.y: dest.y = test.y
    if test.z > dest.z: dest.z = test.z

def vbbmid(vectors):
    r"""
    Returns the mid-point of the bounding box spanned by the list
    of vectors.
    """

    if not vectors:
        return c4d.Vector(0)

    min = c4d.Vector(vectors[0])
    max = c4d.Vector(min)
    for v in vectors:
        vmin(min, v)
        vmax(max, v)

    return (min + max) * 0.5