# coding: utf-8
#
# Copyright (C) 2012, Niklas Rosenstein

import os
import sys
import imp

class Importer(object):
    r"""
    Use this class to enable importing modules from specific
    directories independent from `sys.path`.
    """

    def __init__(self):
        super(Importer, self).__init__()
        self.path = []

    def add(self, *paths):
        r"""
        Add the passed strings to the search-path for importing
        modules. Raises TypeError if non-string object was passed.
        Passed paths are automatically expanded.
        """

        new_paths = []
        for path in paths:
            if not isinstance(path, basestring):
                raise TypeError('passed argument must be string.')
            path = os.path.expanduser(path)
            new_paths.append(path)

        self.path.extend(new_paths)

    def import_(self, name, load_globally=False):
        r"""
        Import the module with the given name from the directories
        added to the Importer. The loaded module will not be inserted
        into `sys.modules` unless `load_globally` is True.
        """

        prev_module = None
        if name in sys.modules and not load_globally:
            prev_module = sys.modules[name]
            del sys.modules[name]

        data = imp.find_module(name, self.path)
        try:
            return imp.load_module(name, *data)
        except:
            data[0].close()
            raise
        finally:
            # Restore the old module or remove the module that was just
            # loaded from `sys.modules` only if we do not load the module
            # globally.
            if not load_globally:
                if prev_module:
                    sys.modules[name] = prev_module
                else:
                    del sys.modules[name]

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
