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
c4dtools.resource
~~~~~~~~~~~~~~~~~
"""

import os
import re
import c4d
import json
import inspect
import warnings
import functools

from c4dtools import utils
from c4dtools import helpers

def load(filename, use_cache=True, cache_suffix='cache'):
    r"""
    Load the symbols of a Cinema 4D resource file. The symbols will be
    loaded directly from the symbols file when *use_cache* is False. In
    the other case, the symbols are loaded from the cached symbols if
    the symbols haven't changed since the cache has been generated. If
    the cache is not available, it will be generated when *use_cache*
    is True.

    The advantage of caching the symbols in a seperate file is the
    improved speed of reading in the symbols.

    *Changed in 1.3.1*: The :func:`load` function now returns a tuple of
    three values instead of two. The ``missing_permissions`` element has been
    added to the end of the tuple.

    .. note::

        The ``missing_permissions`` element of the returned tuple is only
        True if the *use_cache* is passed True **and** the cache could
        not be written.

    :Returns: ``(symbols_dict, changed)``
    :Raises:  OSError if *filename* does not exist or does not point to a
              file.
    """

    if not os.path.isfile(filename):
        raise OSError('passed filename does not exist or does not point to '
                      'a file: %s' % filename)

    cache_name = utils.change_suffix(filename, cache_suffix)

    # Load the cache if desired and available.
    load_from_source = True
    original_changed = False
    load_from_cache = False
    missing_permissions = False

    if use_cache and os.path.isfile(cache_name):
        original_changed = utils.file_changed(filename, cache_name)
        load_from_cache = not original_changed

    if load_from_cache:
        fp = open(cache_name, 'rb')
        data = None
        try:
            data = json.load(fp)
        except ValueError as exc:
            warnings.warn(exc.message + '. Loading symbols from source.')
        finally:
            fp.close()

        if isinstance(data, dict):
            # Convert every key in the dictionary from unicode to
            # a string.
            for key, value in data.items():
                del data[key]
                data[key.encode('utf-8')] = value

            load_from_source = False
            symbols = data
        elif data is not None:
            message = 'loaded %s, expected dict from JSON. Loading symbols ' \
                      'from source.'
            message = message % data.__class__.__name__
            warnings.warn(message)

    # If the cache could not be loaded, load the symbols from the
    # original file.
    if load_from_source:
        fp = open(filename, 'rb')
        try:
            symbols = parse_symbols(fp.read())
        finally:
            fp.close()

        # If the cache should be used, we will now generate it.
        if use_cache:
            try:
                with open(cache_name, 'wb') as cache_fp:
                    json.dump(symbols, cache_fp)
            except IOError as exc:
                missing_permissions = True

    return symbols, original_changed, missing_permissions

def parse_symbols(string):
    r"""
    Parse symbols from the passed string containing the enumerations
    to load.
    """

    # Remove all comments from the source.
    string = ' '.join(line.split('//')[0] for line in string.splitlines())
    string = ' '.join(re.split(r'\/\*.*\*\/', string))

    # Extract all enumeration declarations from the source.
    enumerations = [
        text.split('{')[1].split('}')[0]
        for text in re.split(r'\benum\b', string)[1:]
    ]

    # Load the symbols.
    symbols = {}
    for enum in enumerations:
        last_value = -1
        for name in enum.split(','):
            if '=' in name:
                name, value = name.split('=')
                value = int(value)
            else:
                value = last_value + 1

            name = name.strip()
            if name:
                last_value = value
                symbols[name] = value

    return symbols

class Resource(object):
    r"""
    An instance of this class is used to store the symbols of a
    C4D symbols file and several other information to work with
    the resource of a plugin, such as easily grabbing files from
    that folder, etc.

    .. attribute:: dirname

        The directory name of the resource-folder. Not garuanteed to
        exist!

    .. attribute:: c4dres

        The :class:`c4d.plugins.GeResource` object passed on construction.
        This is usually the ``__res__`` variable passed through from a
        Python plugin.

    .. attribute:: string

        A :class:`StringLoader` instance associated with the resource
        object. Used to load resource strings.

        .. code-block:: python

            # Load a resource-string with the IDC_MYSTRING symbol-name
            # without formatting arguments.
            res.string.IDC_MYSTRING()

            # Or call the str() function on the returned ResourceString
            # instance.
            str(res.string.IDC_MYSTRING)

            # Format the resource string by replacing the hashes in
            # the string with the passed arguments.
            res.string.IDC_FILENOTFOUND(filename)

            # Unpack the tuple returned by the `both` property.
            # Shortcut for:
            #   container.SetString(
            #       res.IDC_CONTEXTMENU_1,
            #       res.string.IDC_CONTEXTMENU_1())
            container.SetString(*res.string.IDC_CONTEXTMENU_1.both)

    The following attributes are only treated correctly if the :func:`load`
    function was used to construct the Resource object.

    .. attribute:: changed

        This attribute is set by the :func:`load` function and is only
        True when the symbols had been cached but the original symbols file
        has been modified. The resource has been reloaded in that case and
        the cache re-written (if specified). If symbol-caching is not
        activated, this field is False always.

        It can be used to recognize the change of a description or symbols
        header file during development.

        The default value of this field is False.

    .. attribute:: missing_permissions

        This field is True if the program has insufficient permissions to
        write any of the caches in :func:`load`.
    """

    @classmethod
    def from_resource_folder(cls, dirname, c4dres, cache=True,
                             parse_description=False):
        r"""
        *New in 1.3.1* Parses a Cinema 4D resource folder structure and
        its descriptions and returns a :class:`Resource` instance.

        :param dirname: The name of the resource directory to parse. It
                should contain a ``c4d_symbols.h`` file, otherwise the
                directory is assumed invalid and the returned Resource
                object contains no symbols at all.
        :param c4dres: A :class:`c4d.plugins.GeResource` instance. Can be
                passed None. This instance will directly correlate to the
                constructor of the :class:`Resource` class.
        :param cache: True if the caching should be done, False if not.
                This parameter is passed to :func:`load`.
        :param parse_description: If this parameter is passed a True
                value, the description resources are parsed additionally
                to the ``c4d_symbols.h`` file.
        :raise OSError: If *dirname* does not point to a directory.
        """

        if not os.path.isdir(dirname):
            raise OSError("'%s' is not a directory." % dirname)

        res = cls(dirname, c4dres, {})

        c4d_symbols = os.path.join(dirname, 'c4d_symbols.h')
        if not os.path.isfile(c4d_symbols):
            return res

        symbols, changed, missing_permissions = load(c4d_symbols, cache)
        res.add_symbols(symbols)
        res.changed |= changed

        if parse_description:
            files = glob.glob(os.path.join(dirname, 'description', '*.h'))
            for filename in files:
                res, changed, perms = load(filename, cache)
                res.add_symbols(symbols)
                res.changed |= changed
                missing_permissions |= perms

        res.missing_permissions = missing_permissions
        return res

    def __init__(self, dirname, c4dres, symbols={}):
        super(Resource, self).__init__()
        self.dirname = dirname
        self.c4dres = c4dres
        self.string = StringLoader(self)
        self.symbols = symbols
        self.changed = False
        self.missing_permissions = False

    def __getattr__(self, name):
        return self.symbols[name]

    def __getitem__(self, name):
        r"""
        *New in 1.3.0*: Shortcut for accessing the :class:`StringLoader`
        in the :class:`Resource` instance. Returns a :class.`ResourceString`
        instance. You can pass a tuple where the first element is a the
        name of the resource symbol and the others serve as substitution.
        """

        if isinstance(name, tuple):
            name, args = name[0], name[1:]
        else:
            args = ()

        return self.string.get(name)(*args)

    @property
    def symbols(self):
        return self._symbols

    @symbols.setter
    def symbols(self, symbols):
        self.highest_symbol = -100000
        self._symbols = {}
        self.add_symbols(symbols)

    def get(self, name):
        r"""
        Returns the value of the symbol with the passed name, or raises
        KeyError if no symbol was found.
        """
        return self.symbols[name]

    def has_symbol(self, name):
        return name in self.symbols

    def add_symbols(self, symbols):
        r"""
        Add the dictionary *symbols* to the resources symbols.

        Raises: TypeError if *symbols* is not a dict instance.
                KeyError if a key in *symbols* is already defined in the
                resource and their value differs.
        """

        utils.ensure_type(symbols, dict)

        res_symbols = self.symbols
        for key, value in symbols.iteritems():
            utils.ensure_type(key, basestring, name='dict-key')
            utils.ensure_type(value, int, name='dict-value')
            if key in res_symbols and res_symbols[key] != value:
                msg = 'key %r already defined in the resource and ' \
                      'the value differs from the updating symbols.'
                raise KeyError(msg % key)
            if value > self.highest_symbol:
                self.highest_symbol = value

        res_symbols.update(symbols)

    def new_symbols(self, *symbols):
        r"""
        *New in 1.3.0*. Adds new symbols to the :class:`Resource` instance.
        Each element in the *\*symbols* parameter may be a string or a tuple.
        If it's a tuple, the name of the symbol is the first name, otherwise
        it will be the string itself. The second element in the tuple must be
        the value.
        """

        l = []
        for symbol in symbols:
            if isinstance(symbol, tuple):
                symbol, value = symbol
            else:
                if self.symbols:
                    value = max(self.symbols.itervalues()) + 1
                else:
                    value = 10000

            self.add_symbols({symbol: value})
            l.append(self.get(symbol))
        return l

    def get_symbol_name(self, id_):
        r"""
        Returns the name of the passed symbol id.
        """

        for k, v in self.symbols.iteritems():
            if v == id_:
                return k

    def file(self, *path_parts):
        r"""
        Concatenate the resource folders path with the passed filename.
        """
        return os.path.join(self.dirname, *path_parts)

class StringLoader(object):
    r"""
    This class is used for conveniently loading strings from the
    c4d_strings.str file. It is basically a wrapper for the
    ``c4d.plugin.GeLoadString`` function. Accessing an attribute on
    an instance of this class will return a callable object accepting
    the same parameters as the previously mentioned API call, but with
    the symbol-id already passed.
    """

    def __init__(self, resource):
        r"""
        Initialize the StringLoader instance with an instance of the
        Resource class.

        Raises: TypeError when *resource* is not a Resource instance.
        """

        if not isinstance(resource, Resource):
            raise TypeError('expected %s.Resource instance.' %
                            inspect.getmodule(Resource))

        self.resource = resource

    def __getattr__(self, name):
        r"""
        Load a string from the resource by the given *name*. Returns
        a :class:`ResourceString` object.

        .. code-block:: python

            id = res.IDC_MYSTRING
            name = res.string.IDC_MYSTRING()
            # same as
            id, name = res.string.IDC_MYSTRING.tuple
        """

        symbol_id = self.resource.get(name)
        return ResourceString(symbol_id, self.resource.c4dres)

    def get(self, name):
        if isinstance(name, int):
            return ResourceString(name, self.resource.c4dres)

        return getattr(self, name)

    def has_symbol(self, name):
        return self.resource.has_symbol(name)

class ResourceString(object):
    r"""
    This class represents a resource-string loaded from plugin resource.
    """

    def __init__(self, id, c4dres):
        super(ResourceString, self).__init__()
        self.id = id
        self.c4dres = c4dres

    def __call__(self, *args):
        r"""
        Wrapper for the :func:`c4d.plugins.GeLoadString` function for
        loading the actual string from the resource.
        """

        string = self.c4dres.LoadString(self.id)

        # Simulate the behaviour of c4d.plugins.GeLoadString by replacing
        # all hashes (`#`) with a passed arguments.
        for arg in args:
            string = string.replace('#', str(arg), 1)

        return string

    def __str__(self):
        r"""
        New in 1.2.8. Equal to :met:`__call__` without passing parameters.
        """

        return self()

    @property
    def both(self):
        r"""
        Returns a tuple of the ``(id, string)`` where *string* is
        loaded from the plugin's resource.
        """
        return self.id, self()


