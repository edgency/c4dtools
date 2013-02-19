# coding: utf-8
#
# Copyright (C) 2012, Niklas Rosenstein

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

    Returns: A dictionary of the loaded symbols.
    Raises:  OSError if *filename* does not exist or does not point to a
             file.
    """

    if not os.path.isfile(filename):
        raise OSError('passed filename does not exist or does not point to '
                      'a file: %s' % filename)

    cache_name = utils.change_suffix(filename, cache_suffix)

    # Load the cache if desired and available.
    load_from_source = True
    load_from_cache = use_cache and os.path.isfile(cache_name) \
        and not utils.file_changed(filename, cache_name)
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
            with open(cache_name, 'wb') as cache_fp:
                json.dump(symbols, cache_fp)

    return symbols

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
    """

    def __init__(self, dirname, symbols):
        super(Resource, self).__init__()
        self.dirname = dirname
        self.symbols = symbols
        self.string = StringLoader(self)

    def __getattr__(self, name):
        return self.symbols[name]

    def get(self, name):
        return self.symbols[name]

    def file(self, filename):
        r"""
        Concatenate the resource folders path with the passed filename.
        """

        return os.path.join(self.dirname, filename)

class StringLoader(object):
    r"""
    This class is used to conveniently loading string from the
    c4d_strings.str file. It is basically a wrapper for the
    `c4d.plugin.GeLoadString` function. Accessing an attribute on
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
        symbol = self.resource.get(name)
        return functools.partial(c4d.plugins.GeLoadString, id=symbol)
