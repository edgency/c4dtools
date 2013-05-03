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
c4dtools.misc.userdata
~~~~~~~~~~~~~~~~~~~~~~

Module for interacting with Cinema 4D's UserData interface.
"""

import c4d
import copy

from c4dtools.utils import ensure_type

class UserDataManager(object):
    r"""
    This class manages userdata-value retrieval and storing.
    It accepts a dictionary associating the attribute-name and
    the userdata's sub-id on initialization and the c4d.BaseList2D
    object to use for retrival and storing.

    The values can optionally be cached to improve value retrieval.

    .. code-block:: python

        from c4dtools.misc.userdata import UserDataSetAndGet as UDSG
        data = UDSG({
            'count': 1,
            'link': 2,
        }, op)
        print data.count
        print data.link
        # Equal to
        print op[c4d.ID_USERDATA, 1]
        print op[c4d.ID_USERDATA, 2]

    *New in 1.2.9*: Renamed to ``UserDataManager`` and added
    type-safety for constructor.
    """

    __slots__ = '_fields _op _cache _do_caching'.split()

    def __init__(self, fields, op, do_caching=True):
        super(UserDataSetAndGet, self).__init__()

        ensure_type(fields, dict)
        ensure_type(op, c4d.BaseObject)

        self._fields = copy.copy(fields)
        self._op = op
        self._cache = {}
        self._do_caching = do_caching

    def __getattr__(self, name):
        if name not in self._fields:
            raise AttributeError('no userdata-field %r defined.' % name)
        if self._do_caching and name in self._cache:
            return self._cache[name]
        value = self._op[c4d.ID_USERDATA, self._fields[name]]
        if self._do_caching:
            self._cache[name] = value
        return value

    def __setattr__(self, name, value):
        if name in self.__slots__:
            super(UserDataSetAndGet, self).__setattr__(name, value)
            return
        elif name not in self._fields:
            raise AttributeError('no userdata-field %r defined.' % name)

        self._op[c4d.ID_USERDATA, self._fields[name]] = value
        if self._do_caching:
            getattr(self, name)

    def clear_cache(self):
        r"""
        Clear the cached values. Call this in case the host object's
        parameters have changed by not using the instance of this class.
        """
        self._cache = {}

# Backwards compatibility for < 1.2.9
UserDataSetAndGet = UserDataManager

