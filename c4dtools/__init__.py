# coding: utf-8
#
# Copyright (C) 2012, Niklas Rosenstein
# Licensed under the GNU General Public License
r"""
c4dtools - A utility library for the Cinema 4D Python API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``c4dtools`` module is a thin Python library created by Niklas Rosenstein.
It provides functions and classes for the everyday work with Python in
Cinema 4D. The most significant feature is the cached parsing of dialog
symbols, see :func:`c4dtools.prepare`.
"""

__version__ = (1, 0, 1)
__author__ = {'name': 'Niklas Rosenstein',
              'email': 'rosensteinniklas@gmail.com'}

import os
import glob

from c4dtools import utils, resource, helpers, plugins, library
from c4dtools.library import load_library

def prepare(filename, cache_symbols=True, libfolder_name='lib',
            resfolder_name='res', parse_descriptions=False):
    r"""
    Call this function from a Cinema 4D python plugin-file (\*.pyp) to
    set up convenient data that can be used from the plugin.

    :Parameters:
        - filename: Just pass the ``__file__`` variable from the plugins
          global scope.
        - cache_symbols: True by default. Defines wether the resource
          symbols will be cached.
        - libfolder_name: The name of the folder the plugin related
          libraries are stored. The returned Importer instance will
          be able to load python modules and packages from this
          directory.
        - resfolder_name: The name of the plugins resource folder. This
          usually does not need to be changed as the name of this folder
          is defined by Cinema 4D.
        - parse_descriptions: False by default. When True, description
          resource symbols will parsed additionally to the dialog
          resource symbols. Note that strings can *not* be loaded from
          symbols of description resources.
    :Returns: A tuple of two elements.

             0. :class:`c4dtools.resource.Resource` instance.
             1. :class:`c4dtools.utils.Importer` instance.
    """

    path = helpers.Attributor()
    path.root = os.path.dirname(filename)
    path.res = resfolder_name
    path.lib = libfolder_name

    if not os.path.isabs(path.res):
        path.res = os.path.join(path.root, path.res)
    if not os.path.isabs(path.lib):
        path.lib = os.path.join(path.root, path.lib)

    path.c4d_symbols = os.path.join(path.res, 'c4d_symbols.h')
    path.description = os.path.join(path.res, 'description')

    importer = utils.Importer()

    if os.path.isdir(path.lib):
        importer.add(path.lib)

    symbols_container = resource.Resource(path.res, {})

    if os.path.isfile(path.c4d_symbols):
        symbols = resource.load(path.c4d_symbols, cache_symbols)
        symbols_container.add_symbols(symbols)

    if parse_descriptions:
        files = glob.glob(os.path.join(path.description, '*.h'))
        for filename in files:
            symbols = resource.load(filename, cache_symbols)
            symbols_container.add_symbols(symbols)

    return (symbols_container, importer)
