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
c4dtools - A utility library for the Cinema 4D Python API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``c4dtools`` module is a thin Python library created by Niklas Rosenstein.
It provides functions and classes for the everyday work with Python in
Cinema 4D. The most significant feature is the cached parsing of dialog
symbols, see :func:`c4dtools.prepare`.
"""

__version__ = (1, 3, 0, 'final')
__author__ = {'name': 'Niklas Rosenstein',
              'email': 'rosensteinniklas@gmail.com'}

import os
import sys
import c4d
import glob

from c4dtools import utils, resource, helpers, plugins, library, importer
from c4dtools.library import load_library

def prepare(filename=None, c4dres=None, cache=True,
            libfolder_name='lib', resfolder_name='res',
            parse_description=False, imp_store_modules=True):
    r"""
    Call this function from a Cinema 4D python plugin-file (``*.pyp``) to
    set up convenient data that can be used from the plugin.

    .. code-block:: python

        import c4d
        import c4dtools

        res, imp = c4dtools.prepare(__file__, __res__)

        # ...

    :param filename:

        Just pass the ``__file__`` variable from the plugins global
        scope.

        *New in 1.3.0*: Default value added. The filename will
        be retrieved using the globals of the frame that has called
        the function if *None* was passed.

    :param c4dres:

        The :class:`c4d.plugins.GeResource` instance from the
        plugin's scope.

        *New in 1.2.6*: Default value added. The plugin resource
        will be retrieved using the globals of the frame that
        has called the function if *None* was passed.

    :param cache:

        True by default. Defines wether the resource symbols will
        be cached.

    :param libfolder_name:

        The name of the folder the plugin related libraries are
        stored. The returned Importer instance will be able to load
        python modules and packages from this directory.

    :param resfolder_name:

        The name of the plugins resource folder. This usually does
        not need to be changed as the name of this folder is defined
        by Cinema 4D.

    :param parse_description:

        False by default. When True, description resource symbols will
        parsed additionally to the dialog resource symbols. Note that
        strings can *not* be loaded from symbols of description
        resources.

    :param imp_store_modules:

        Passed to the constructor of the returned :class:`Importer`,
        defining whether imported modules are stored or not.

    :return:

        A tuple of two elements:

        - :class:`c4dtools.resource.Resource`
        - :class:`c4dtools.utils.Importer`

    *New in 1.3.0*: Added *imp_store_modules* parameter.
    """

    globals_ = sys._getframe().f_back.f_globals
    if filename is None:
        filename = globals_.get('__file__', None)
        if not filename:
            raise ValueError('filename could not be retrieved from the '
                             'calling frame.')
    if c4dres is None:
        c4dres = globals_.get('__res__', None)

    utils.ensure_type(filename, basestring, name='filename')
    utils.ensure_type(c4dres, c4d.plugins.GeResource, type(None), name='c4dres')

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

    imp = importer.Importer(store_modules=imp_store_modules)

    if os.path.isdir(path.lib):
        imp.add(path.lib)

    symbols_container = resource.Resource(path.res, c4dres, {})

    if os.path.isfile(path.c4d_symbols):
        symbols, changed = resource.load(path.c4d_symbols, cache)
        symbols_container.add_symbols(symbols)
        symbols_container.changed |= changed

    if parse_description:
        files = glob.glob(os.path.join(path.description, '*.h'))
        for filename in files:
            symbols, changed = resource.load(filename, cache)
            symbols_container.add_symbols(symbols)
            symbols_container.changed |= changed

    return (symbols_container, imp)
