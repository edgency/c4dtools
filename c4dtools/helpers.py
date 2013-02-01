# coding: utf-8
#
# Copyright (C) 2012, Niklas Rosenstein
# Licensed under the GNU General Public License
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
