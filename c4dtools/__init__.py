# coding: utf-8
#
# Copyright (C) 2012, Niklas Rosenstein

import os

from c4dtools import utils
from c4dtools import resource
from c4dtools import helpers
from c4dtools import plugins

def prepare(filename, cached_res=True, libfolder_name='lib',
            resfolder_name='res'):
    r"""
    Call this function from a Cinema 4D python plugin-file (*.pyp) to
    set up convenient data that can be used from the plugin.

    Returns: A tuple of two elements.
             0.: `c4dtools.resource.Resource` instance or None.
             1.: `c4dtools.helpers.Importer` instance.
    """

    path = helpers.Attributor()
    path.root = os.path.dirname(filename)
    path.res = os.path.join(path.root, resfolder_name)
    path.lib = os.path.join(path.root, libfolder_name)
    path.c4d_symbols = os.path.join(path.res, 'c4d_symbols.h')

    symbols_container = None
    if os.path.isfile(path.c4d_symbols):
        symbols = resource.load(path.c4d_symbols, cached_res)
        symbols_container = resource.Resource(path.res, symbols)

    importer = helpers.Importer()
    if os.path.isdir(path.lib):
        importer.add(path.lib)

    return (symbols_container, importer)
