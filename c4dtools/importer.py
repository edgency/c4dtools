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
c4dtools.importer
~~~~~~~~~~~~~~~~~

*New in 1.3.0*. Implements a class for safely importing packages. The
contents of this package was previously defined in :mod`c4dtools.utils`.
"""

import os
import sys
import copy

def get_root_module(modname, suffixes='pyc pyo py'.split()):
    r"""
    *New in 1.2.6*.

    Returns the root-file or folder of a module filename. The return-value
    is a tuple of ``(root_path, is_file)``.

    *New in 1.3.0*: Moved to :mod:`c4dtools.importer`.
    """

    dirname, basename = os.path.split(modname)

    # Check if the module-filename is part of a Python package.
    in_package =  False
    for sufx in suffixes:
        init_mod = os.path.join(dirname, '__init__.%s' % sufx)
        if os.path.exists(init_mod):
            in_package = True
            break

    # Go on recursively if the module is in a package or return the
    # module path and if it is a file.
    if in_package:
        return get_root_module(dirname)
    else:
        return os.path.normpath(modname), os.path.isfile(modname)

class Importer(object):
    r"""
    Use this class to enable importing modules from specific
    directories independent from ``sys.path``.

    .. attribute:: high_priority

        When this value is True, the paths defined in the importer are
        prepended to the original paths in ``sys.path``. If False, they
        will be appended. Does only have an effect when :attr:`use_sys_path`
        is True.

    .. attribute:: use_sys_path

        When this value is ``True``, the original paths from ``sys.path``
        are used additionally to the paths defined in the imported.

    .. attribute:: modules

        A dictionary containing the modules that have been imported
        with the instance of the :class:`Importer`. Can be ``None``
        when *store_modules* was passed ``False`` on initialization.

    *New in 1.3.0*:

        - Moved to :mod:`c4dtools.importer`
        - Added :attr:`modules` attribute
    """

    def __init__(self, high_priority=False, use_sys_path=True,
                 store_modules=True):
        super(Importer, self).__init__()
        self.path = []
        self.use_sys_path = use_sys_path
        self.high_priority = high_priority

        if store_modules:
            self.modules = {}
        else:
            self.modules = None

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
            new_paths.append(os.path.normpath(path))

        self.path.extend(new_paths)

    def is_local(self, module):
        r"""
        Returns True if the passed module object can be found in the
        paths defined in the importer, False if not.
        """

        if not hasattr(module, '__file__'):
            return False

        modpath = os.path.dirname(get_root_module(module.__file__)[0])
        return modpath in self.path

    def import_(self, name):
        r"""
        Import the module with the given name from the directories
        added to the Importer. The loaded module will not be inserted
        into `sys.modules`.
        """

        with self.protected():
            m = __import__(name)
            for n in name.split('.')[1:]:
                m = getattr(m, n)
            return m

    def protected(self):
        r"""
        New in 1.3.0. Return an object implementing the with-interface
        creating a protected environment for importing modules. The
        with-entrance does not return any value.

        .. code-block:: python

            with imp.protected():
                import module_a
                import module_b
        """

        return ProtectedEnvironment(self)

    def _store_module(self, name, module):
        r"""
        Private. Stores a module in the dictionary modules dictionary
        of the importer.
        """

        if self.modules is not None:
            self.modules[name] = module

class ProtectedEnvironment(object):

    def __init__(self, importer):
        super(ProtectedEnvironment, self).__init__()
        self.importer = importer

    def __enter__(self):
        importer = self.importer

        # Store the previous path and module configuration.
        self.prev_path = copy.copy(sys.path)
        self.prev_modules = copy.copy(sys.modules)

        # Modify `sys.path`.
        if importer.use_sys_path:
            if importer.high_priority:
                sys.path = importer.path + sys.path
            else:
                sys.path = sys.path + importer.path

        # Add the stored modules of the importer to the
        # system modules dictionary.
        if importer.modules:
            sys.modules.update(importer.modules)

        return None

    def __exit__(self, exc_type, exc_value, exc_tb):
        importer = self.importer

        # Restore the previous `sys.path` configuration.
        sys.path = self.prev_path

        # Restore the old module configuration. Only modules that have
        # not been in `sys.path` before will be removed.
        for k, v in sys.modules.items():
            if k not in self.prev_modules and importer.is_local(v) or not v:
                self.importer._store_module(k, v)
                del sys.modules[k]
            else:
                sys.modules[k] = v


