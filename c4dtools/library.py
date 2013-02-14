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
c4dtools.library
~~~~~~~~~~~~~~~~

This module implements functionality for making it possible for
plugins to interface with each other, i.e. one plugin may depend
on the functionality of another plugin (even developed from different
developers).

A Python plugin may create a Library class that will be (automatically)
registered to the c4dtools.library mmodule. This library can then be
loaded from another plugin to establish a Python-level communication
between these plugins. As the plugin initialization order can not be
controlled from Python, and there may also exist a circular reference
to libraries of two or more plugins, references to libraries are always
lazy and loaded on-request.

Example library:

.. code-block:: python

    import c4dtools

    class MyLibrary(c4dtools.library.Library):

        class Meta:
            # Here comes meta information.
            pass

        def on_create(self):
            print "MyLibrary has been created."

        def on_install(self, name):
            print "MyLibrary has been installed under the name %s." % name

        def get_stuff(self):
            return "This is from MyLibrary!"

Nothing more needs to be done. The library is automatically registered
with the name ``'MyLibrary'``. The name the library is registered with
can be changed by defining `name='libname'` in the Meta section. When
registration should be prevented, one needs to define ``abstract=True``
in the Meta section.

This library can now be loaded from another Python unit.

.. code-block:: python

    import c4dtools
    MyLibrary = c4dtools.load_library('MyLibrary')
    print MyLibrary.get_stuff()
"""

import copy
import types

from c4dtools.utils import clsname
from c4dtools.helpers import Attributor

class LibraryNotFound(Exception):
    r"""
    This exception is thrown when a requested library was not found.
    """

class LibraryMeta(type):
    r"""
    This is the meta-class of the Library class. It implements
    automatically registering the Library when the class is
    created, except it is marked as abstract.

    One can mark a Library as abstract when defining a meta-object
    on class-level that contains an attribute ``abstract`` that
    evaluates to True. A library must be marked abstract explicitly.
    An abstract library will *not* be registered.

    Example:

    .. code-block:: python

        class MyLibrary(Library):
            class Meta:
                abstract = True
            # ...
    """

    __meta_default = {
        'abstract': False,
        'name': None,
        'allow_overwrite': False,
    }

    __installed = {}

    def __new__(self, name, bases, dict):
        super_new = super(LibraryMeta, self).__new__

        # Disallow instantiation of the class.
        def __init__(self):
            raise NotImplementedError
        dict['__init__'] = __init__

        # If this isn't a subclass of Library, we don't have a thing
        # to do more.
        parents = [base for base in bases if isinstance(base, LibraryMeta)]
        if not parents:
            return super_new(self, name, bases, dict)

        # Process the defined Meta information and fill in the defaults.
        meta = self.__meta_default.copy()
        if 'Meta' in dict:
            meta.update(vars(dict.pop('Meta')))

        meta = Attributor(meta)
        dict['Meta'] = meta

        # The libraries name defaults to its class-name.
        if not meta.name:
            meta.name = name

        # Turn all functions that would be turned into instance methods
        # into class methods.
        for key, value in dict.items():
            if isinstance(value, types.FunctionType):
                dict[key] = classmethod(value)

        # Create the class and call its on_create() method.
        library = super_new(self, name, bases, dict)
        library.on_create()

        # Register the Library class if it is *not* abstract.
        if not meta.abstract:
            if meta.name in self.__installed:
                existing = self.__installed[meta.name]
                if not existing.Meta.allow_overwrite:
                    msg = 'library with name %r is already installed.' % \
                          meta.name
                    raise RuntimeError(msg)

            self.__installed[meta.name] = library
            library.on_install(meta.name)

        return library

    def on_create(self):
        r"""
        This class method is called when the library class instance
        was created.
        """
        pass

    def on_install(self, name):
        r"""
        This class method is called when the library is installed.
        This method will not be called when the library is marked as
        abstract.
        """
        pass

    @classmethod
    def get_library(self, name):
        r"""
        Finds and returns an installed library with the passed name.

        Raises: LibraryNotFound when there is not library with this
                name installed.
        """

        if not name in self.__installed:
            raise LibraryNotFound('no library with name %r installed.' % name)

        return self.__installed[name]

class Library(object):
    r"""
    This is the base class for library objects. It's metaclass
    ``LibraryMeta`` will automatically turn methods into classmethods
    and will disallow the instantiaton of the class.
    """

    __metaclass__ = LibraryMeta

class LazyLibrary(object):
    r"""
    This class is representing a lazy reference to a library. The actual
    library will be loaded on the first request.
    """

    def __init__(self, libname):
        super(LazyLibrary, self).__init__()
        self.__libname = libname

    @property
    def __library(self):
        self.__library = load_library(self.__libname)

        # Write each value from the loaded library into the
        # LazyLibrary so __getattr__ does not need to be called
        # anymore.
        for attrname in dir(self.__library):
            setattr(self, attrname, getattr(self.__library, attrname))

    def __getattr__(self, name):
        return getattr(self.__library, name)

def load_library(name, lazy=False):
    r"""
    Load a library. Returns a :class:`Library` instance unless *lazy*
    does not evaluate to True. If *lazy* is True, a :class:`LazyLibrary`
    instance will be returned.
    """
    if lazy:
        return LazyLibrary(name)
    else:
        return LibraryMeta.get_library(name)

