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
c4dtools.misc.dialogs
~~~~~~~~~~~~~~~~~~~~~

New in 1.2.8. This module allows you to store and retrieve data from
a dialog dynamically, creating a dictionary or :class:`c4d.BaseContainer`
from this data and also loading this data back.
"""

import abc
import c4d
import collections

from c4d import BaseContainer
from c4d.gui import GeDialog
from c4dtools.utils import ensure_type, ensure_value

class Datatype(object):
    r"""
    This class represents a datype used in the :class:`DialogContainer`
    class. It acts as worker for retreiving, setting and converting data.
    """

    __metaclass__ = abc.ABCMeta

    # Set this to the identifier for the datatype used in the
    # :methd:`DialogContainer.add` method.
    identifier = None

    @abc.abstractmethod
    def get_value(self, dialog, symbol ):
        r"""
        Retrieve the value of the parameter identified by the integral
        *symbol* from the :class:`c4d.GeDialog` *dialog*.
        """
        pass

    @abc.abstractmethod
    def set_value(self, dialog, symbol, value):
        r"""
        Set the Python object *value* for the passed *symbol* to the
        :class:`c4d.GeDialog` *dialog*.
        """
        pass

    @abc.abstractmethod
    def from_container(self, symbol, container):
        r"""
        Read the value of *symbol* from the *container* (a
        :class:`c4d.BaseContainer` instance) and convert it to a Python
        object.

        .. note:: *symbol* might not be exactly the same value as it
                  was passed to :meth:`DialogContainer.add`.
        """
        pass

    @abc.abstractmethod
    def to_container(self, symbol, container, value):
        r"""
        Convert the Python object *value* to a datatype that can be
        stored in the :class:`c4d.BaseContainer` *container*. The
        function is responsible for storing the value in the
        container.

        .. note:: *symbol* might not be exactly the same value as it
                  was passed to :meth:`DialogContainer.add`.
        """
        pass

class DialogContainer(object):
    r"""
    This class is used to store the configuration of a
    :class:`c4d.gui.GeDialog` is a :class:`c4d.BaseContainer` object.
    It requires an initialization step to associate resource symbols
    with the data-type.

    Here's an example:

    .. code-block:: python

        import c4d
        import c4dtools
        from c4d import BaseContainer
        from c4d.plugins import GetWorldPluginData, SetWorldPluginData
        from c4dtools.misc.dialog import DialogContainer

        res, _ = c4dtools.prepare(__file__, __res__)

        class MyDialog(c4d.gui.GeDialog):

            # Must be a unique plugincafe identifier, used in
            # InitValues and DestroyWindow!
            ID = 1027195

            container = None

            def __init__(self):
                super(MyDialog, self).__init__()

                # Initialize the container.
                c = DialogContainer()
                add = c.add

                add('optimize', res.CHK_OPTIMIZE, 'b')
                add('optimize_tolerance', res.EDT_OPTIMIZE_TOLERANCE, 'f')
                add('scenefile', res.FLN_SCENE, 'fl')
                add('mode', res.CMB_MODE, 'l')

                self.container = c

            def __getattr__(self, name):
                return self.container.get(self, name)

            def __call__(self, name, value):
                self.container.set(self, name, value)

            # c4d.gui.GeDialog

            def CreateLayout(self):
                return self.LoadDialogResource(res.DLG_MAIN)

            def InitValues(self):
                self('optimize', True)
                self('optimize_tolerance', 0.01)
                self('scenefile', '')
                self('mode', res.CMB_MODE_DEFAULT)

                # Load a container that stores the dialog configuration.
                bc = GetWorldPluginData(MyDialog.ID) or BaseContainer()
                print self.container.load_container(self, bc, genlist=True)

                return True
            def AskClose(self):
                # Save the dialog configuration !
                if getattr(self, 'container', None):
                    bc = self.container.to_container(self)
                    SetWorldPluginData(MyDialog.ID, bc)
                return False

            def Command(self, id, msg):
                print "Dialog Values:",
                print self.optimize, self.optimize_tolerance,
                print self.scenefile, self.mode
                return True

        dlg = MyDialog()
        dlg.Open(c4d.DLG_TYPE_MODAL)
    """

    def __init__(self):
        super(DialogContainer, self).__init__()
        self._data = {}
        self._types = {}

        self.on_init()

    def on_init(self):
        r"""
        Called after :meth:`__init__` has finished. The default
        implementation adds the default datatypes.
        """

        self.register_datatype(BoolDatatype())
        self.register_datatype(RealDatatype())
        self.register_datatype(MeterDatatype())
        self.register_datatype(DegreeDatatype())
        self.register_datatype(PercentDatatype())
        self.register_datatype(LongDatatype())
        self.register_datatype(StringDatatype())
        self.register_datatype(FilenameDatatype())
        self.register_datatype(TimeDatatype())

    def register_datatype(self, datatype):
        r"""
        Register a new data-type that will be available for the :meth:`add`
        method.
        """

        ensure_type(datatype, Datatype)
        if not datatype.identifier:
            raise ValueError('passed Datatype instance has not identifier set.')
        if datatype.identifier in self._types:
            raise RuntimeError('passed Datatype identifier already occupied.')

        self._types[datatype.identifier] = datatype

    def add(self, param_name, symbol, param_type):
        r"""
        Let the container know about a new parameter. *param_name*
        must be a string that will be used to access the parameter via
        the dialog container.

        *symbol* must be an integer used to identify the parameter
        in the dialog.

        *param_type* must be either a string identifieng the data-type
        of the parameter or a sequence of 2 or 4 elements. When passing
        an sequence type the first two elements are always 1. the
        getter of the parameter 2. the setter of the parameter. The getter
        function is passed the integral *symbol* passed to this method
        and the dialog to retrieve the value from. The setter is additionally
        passed the value to set.

        When the sequence has not 2 elements, it must have 4.
        :class:`ValueError` is raised otherwise. The last 2 elements of
        the sequence must be a converter from and to data of a
        :class:`c4d.BaseContainer`. The converter from the container to
        Python object is passed ``(symbol, container)`` and the converter
        from Python object to container is passed
        ``(symbol, container, value)``. The function itself is responsible
        for storing the symbol in the container.

        If *param_type* is not a sequence type, it must be a string
        identifieng the parameter data type. Possible values are:

        =============================== =================
        Data Type                       String Identifier
        =============================== =================
        Bool (:class:`bool`)            ``'b'``
        Real (:class:`float`)           ``'f'``
        Meter (:class:`float`)          ``'m'``
        Degree (:class:`float`)         ``'d'``
        Percent (:class:`float`)        ``'p'``
        Long (:class:`int`)             ``'i'``
        String (:class:`str`)           ``'s'``
        Filename (:class:`str`)         ``'fl'``
        Time (:class:`c4d.BaseTime`)    ``'t'``

        These are the standart types. More types can be registered via
        :meth:`register_datatype`.
        """

        if param_type not in self._types:
            message = 'no Datatype registered with identifier %r' % param_type
            raise ValueError(message)

        if param_name in self._data:
            raise ValueError('parameter %r already registered.' % param_name)

        self._data[param_name] = (symbol, self._types[param_type])

    def get(self, dialog, name):
        r"""
        Retrieve a parameter from the dialog.
        """

        symbol, datatype = self._data[name]
        return datatype.get_value(dialog, symbol)

    def set(self, dialog, name, value):
        r"""
        Set a parameter to the dialog.
        """

        symbol, datatype = self._data[name]
        datatype.set_value(dialog, symbol, value)

    def to_dict(self, dialog, names=(), mode='exclude'):
        r"""
        Creates a dictionary of all values stored in the container.
        *exclude* may be a sequence type containing the names to exclude
        from the dictionary. *include* may contain the names to include
        in the dictionary.

        *include* has precedence over *exclude*.
        """

        ensure_value(mode, 'include', 'exclude', name='mode')
        if mode == 'exclude':
            def check(n): return n not in names
        elif mode == 'include':
            def check(n): return n in names

        result = {}
        for name, (symbol, datatype) in self._data.iteritems():
            if check(name):
                result[name] = datatype.get_value(dialog, symbol)

        return result

    def load_dict(self, dialog, data, genlist=False):
        r"""
        Set values from a Python dictionary to the dialog. If *genlist*
        is True, a list of names is generated that have been set from
        the passed *data*.
        """

        ensure_type(data, dict)

        names = []
        for name, value in data.iteritems():
            symbol, datatype = self._data[name]
            datatype.set_value(dialog, symbol, value)

            if genlist:
                names.append(name)

        return names

    def to_container(self, dialog, names=(), mode='exclude'):
        r"""
        Just like :meth`to_dict` but creates a :class:`c4d.BaseContainer`
        instance.
        """

        ensure_value(mode, 'include', 'exclude', name='mode')
        if mode == 'exclude':
            def check(n): return n not in names
        elif mode == 'include':
            def check(n): return n in names

        data = BaseContainer()
        for name, (symbol, datatype) in self._data.iteritems():
            if check(name):
                value = datatype.get_value(dialog, symbol)
                datatype.to_container(symbol, data, value)

        return data

    def load_container(self, dialog, container, genlist=False):
        r"""
        Just like :meth:`load_dict` but *container* is a
        :class:`c4d.BaseContainer` instance. If *genlist* is True, a list of
        names is generated that have been set from the passed *data*.
        """

        ensure_type(container, BaseContainer)

        # Rework the data dictionary to associate the symbols
        # with the datatypes.
        data = {}
        for name, (symbol, datatype) in self._data.iteritems():
            data[symbol] = datatype, name

        names = []
        for symbol, value in container:
            datatype, name = data[symbol]
            value = datatype.from_container(symbol, container)
            datatype.set_value(dialog, symbol, value)

            if genlist:
                names.append(name)

        return names


class FunctionBoundDatatype(Datatype):

    d_default = None
    c_default = None
    d_getter = None
    d_setter = None
    c_getter = None
    c_setter = None

    def __init__(self, d_getter=None, d_setter=None, c_getter=None,
                 c_setter=None):
        super(FunctionBoundDatatype, self).__init__()

        self.on_init()

        if d_getter:
            self.d_getter = d_getter
        if d_setter:
            self.d_setter = d_setter
        if c_getter:
            self.c_getter = c_getter
        if c_setter:
            self.c_setter = c_setter

    def on_init(self):
        r"""
        Calld *before* anything is done in :meth:`__init__`. Only the
        parent call was made before.
        """
        pass

    # Datatype

    def get_value(self, dialog, symbol):
        v = self.d_getter(dialog, symbol) or self.d_default
        if v is None:
            v = self.d_default
        return v

    def set_value(self, dialog, symbol, value):
        self.d_setter(dialog, symbol, value)

    def from_container(self, symbol, container):
        return self.c_getter(container, symbol, self.c_default)

    def to_container(self, symbol, container, value):
        self.c_setter(container, symbol, value)

class BoolDatatype(FunctionBoundDatatype):

    # FunctionBoundDatatype

    d_default = False
    c_default = False

    def on_init(self):
        self.d_getter = GeDialog.GetBool
        self.d_setter = GeDialog.SetBool
        self.c_getter = BaseContainer.GetBool
        self.c_setter = BaseContainer.SetBool

    # Datatype

    identifier = 'b'

class RealDatatype(FunctionBoundDatatype):

    # FunctionBoundDatatype

    d_default = 0.0
    c_default = 0.0

    def on_init(self):
        self.d_getter = GeDialog.GetReal
        self.d_setter = GeDialog.SetReal
        self.c_getter = BaseContainer.GetReal
        self.c_setter = BaseContainer.SetReal

    # Datatype

    identifier = 'f'

class MeterDatatype(RealDatatype):

    # FunctionBoundDatatype

    def on_init(self):
        super(MeterDatatype, self).on_init()
        self.d_setter = GeDialog.SetMeter

    # Datatype

    identifier = 'm'

class DegreeDatatype(RealDatatype):

    # FunctionBoundDatatype

    def on_init(self):
        super(DegreeDatatype, self).on_init()
        self.d_setter = GeDialog.SetDegree

    # Datatype

    identifier = 'd'

class PercentDatatype(RealDatatype):

    # FunctionBoundDatatype

    def on_init(self):
        super(PercentDatatype, self).on_init()
        self.d_setter = GeDialog.SetPercent

    # Datatype

    identifier = 'p'

class LongDatatype(FunctionBoundDatatype):

    # FunctionBoundDatatype

    d_default = 0
    c_default = 0

    def on_init(self):
        self.d_getter = GeDialog.GetLong
        self.d_setter = GeDialog.SetLong
        self.c_getter = BaseContainer.GetLong
        self.c_setter = BaseContainer.SetLong

    # Datatype

    identifier = 'l'

class StringDatatype(FunctionBoundDatatype):

    # FunctionBoundDatatype

    def on_init(self):
        self.d_getter = GeDialog.GetString
        self.d_setter = GeDialog.SetString
        self.c_getter = BaseContainer.GetString
        self.c_setter = BaseContainer.SetString

    # Datatype

    identifier = 's'

class FilenameDatatype(FunctionBoundDatatype):

    # FunctionBoundDatatype

    def on_init(self):
        self.d_getter = GeDialog.GetFilename
        self.d_setter = GeDialog.SetFilename
        self.c_getter = BaseContainer.GetFilename
        self.c_setter = BaseContainer.SetFilename

    # Datatype

    identifier = 'fl'

class TimeDatatype(FunctionBoundDatatype):

    # FunctionBoundDatatype

    def on_init(self):
        self.d_getter = GeDialog.GetTime
        self.d_setter = GeDialog.SetTime
        self.c_getter = BaseContainer.GetTime
        self.c_setter = BaseContainer.SetTime

    # Datatype

    identifier = 't'


