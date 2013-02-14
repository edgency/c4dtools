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
c4dtools.helpers
~~~~~~~~~~~~~~~~

This module defines content that has a rather generic purpose, unlike
the contents of the :mod:`c4dtools.utils` module.
"""

class Attributor(object):
    r"""
    Instances of this class will allow setting and getting any value
    from the dictionary passed on construction. The dictionary is
    stored in the `dict_` slot of the instance.
    """

    __slots__ = ('dict_',)

    def __init__(self, dict_=None):
        if dict_ is None:
            dict_ = {}
        self.dict_ = dict_

    def __getattr__(self, name):
        return self.dict_[name]

    def __setattr__(self, name, value):
        if name in Attributor.__slots__:
            return super(Attributor, self).__setattr__(name, value)
        else:
            self.dict_[name] = value

    def __add__(self, another_dict):
        r"""
        Merge the passed dictionary with the values from the Attributor
        instance. Raises TypeError if *another_dict* is not a dict
        or Attributor instance.
        """

        if isinstance(another_dict, Attributor):
            another_dict = another_dict.dict_
        if not isinstance(another_dict, dict):
            raise TypeError('expected dictionary.')

        self.dict_.update(another_dict)

    def __copy__(self):
        return Attributor(copy.copy(self.dict_))

    def __deepcopy__(self):
        return Attributor(copy.deepcopy(self.dict_))
