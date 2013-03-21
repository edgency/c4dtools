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
c4dtools.utils
~~~~~~~~~~~~~~
"""

import os
import sys
import c4d
import time
import threading
import collections

# =============================================================================
#                                Path operations
# =============================================================================

def change_suffix(filename, new_suffix):
    r"""
    Replaces the suffix of the passed filename with *new_suffix*.
    """

    index = filename.rfind('.')
    if index >= 0:
        filename = filename[:index]

    return '%s.%s' % (filename, new_suffix)

def file_changed(original, copy):
    r"""
    Returns True when the filename pointed by *original* was modified
    before the last time *copy* was modified, False otherwise.
    """

    return os.path.getmtime(original) > os.path.getmtime(copy)

# =============================================================================
#                               Vector operations
# =============================================================================

def vmin(dest, test):
    r"""
    For each component of the vectors *dest* and *test*, this function
    writes the lower value of each pairs into the respective component
    of *dest*.
    """

    if test.x < dest.x: dest.x = test.x
    if test.y < dest.y: dest.y = test.y
    if test.z < dest.z: dest.z = test.z

def vmax(dest, test):
    r"""
    For each component of the vectors *dest* and *test*, this function
    writes the upper value of each pairs into the respective component
    of *dest*.
    """

    if test.x > dest.x: dest.x = test.x
    if test.y > dest.y: dest.y = test.y
    if test.z > dest.z: dest.z = test.z

def vbbmid(vectors):
    r"""
    Returns the mid-point of the bounding box spanned by the list
    of vectors. This is different to the arithmetic middle of the
    points.

    Returns: :class:`c4d.Vector`
    """

    if not vectors:
        return c4d.Vector(0)

    min = c4d.Vector(vectors[0])
    max = c4d.Vector(min)
    for v in vectors:
        vmin(min, v)
        vmax(max, v)

    return (min + max) * 0.5

# =============================================================================
#                               Several utilities
# =============================================================================

def clsname(obj):
    r"""
    Return the name of the class of the passed object. This is a shortcut
    for ``obj.__class__.__name__``.
    """

    return obj.__class__.__name__

def candidates(value, obj, callback=lambda vref, vcmp, kcmp: vref == vcmp):
    r"""
    Searches for *value* in *obj* and returns a list of all keys where
    the callback returns True, being passed *value* as first argument,
    the value to compare it with as the second argument and the name
    of the attribute as the third.

    Returns: list of str
    """

    results = []
    for k, v in vars(obj).iteritems():
        if callback(value, v, k):
            results.append(k)

    return results

def ensure_type(x, *types, **kwargs):
    r"""
    New in 1.2.5.

    This function is similar to the built-in :func:`isinstance` function
    in Python. It accepts an instance of a class as first argument, namely
    *x*, and checks if it is an instance of one of the passed types. The
    types must not be encapsulated in a tuple (which is in contrast to
    the :func:`isinstance` method).

    This function raises a :class:`TypeError` exception with a proper
    error message when *x* is not an instance of the passed *\*types*.

    *Changed in 1.2.8*: Renamed from *assert_type* to *ensure_type*. Added
    *\*\*kwargs* parameter. Pass ``name`` as keyword-argument for adding
    the parameter    name that was wrong in the message.
    """

    name = kwargs.pop('name', None)
    for k, v in kwargs:
        raise TypeError("unexpected keyword argument '%r'" % k)

    if not types:
        pass
    elif not isinstance(x, types):
        names = []
        for t in types:
            names.append(t.__module__ + '.' + t.__name__)

        if len(names) > 1:
            message = 'xpected instance of %s, got %s'
            first = ', '.join(names[:-1]) + ' or ' + names[-1]
        else:
            message = 'xpected instance of type %s, got %s'
            first = names[0]

        if name:
            message = 'Invalid type for parameter %r, e' % name + message
        else:
            message = 'E' + message

        cls = x.__class__
        message = message % (first, cls.__module__ + '.' + cls.__name__)
        raise TypeError(message)

assert_type = ensure_type # Backwards compatibility for < 1.2.8

def ensure_value(x, *values, **kwargs):
    r"""
    New in 1.2.8.

    This function checks if the value *x* is in *\*values*. If this does
    not result in True, :class:`ValueError` is raised.

    Pass ``name`` as keyword-argument to specify the parameter name that
    was given wrong in the message.
    """

    name = kwargs.pop('name', None)
    for k in kwargs:
        raise TypeError("unexpected keyword argument %r" % k)

    if not values:
        pass

    if x not in values:
        if len(values) > 1:
            message = 'Possible values are %r' % list(values)
        else:
            message = 'Expected value is %r' % values[0]

        if name:
            message = 'Invalid value for parameter %r, ' + message
            message = message % name

        raise ValueError(message)

def get_root_module(modname, suffixes='pyc pyo py'.split()):
    r"""
    New in 1.2.6.

    Returns the root-file or folder of a module filename. The return-value
    is a tuple of ``(root_path, is_file)``.
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

# =============================================================================
#                                  Decorators
# =============================================================================

def func_attr(**attrs):
    r"""
    New in 1.2.6.

    This decorator must be called, passing attributes to be stored in the
    decorated function.
    """

    def wrapper(func):
        for k, v in attrs.iteritems():
            setattr(func, k, v)
        return func

    return wrapper

# =============================================================================
#              Cinema 4D related stuff, making common things easy
# =============================================================================

def flush_console(id=13957):
    r"""
    Flushes the Cinema 4D console.
    """

    c4d.CallCommand(id)

def update_editor():
    r"""
    A shortcut for

    .. code-block:: python

        c4d.DrawViews(
                c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD |
                c4d.DRAWFLAGS_NO_REDUCTION | c4d.DRAWFLAGS_STATICBREAK)

    Can be used to update the editor, useful for going through the frames
    of a document and doing backing or similar stuff.

    :Returns: The return-value of :func:`c4d.DrawViews`.
    """

    return c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD |
            c4d.DRAWFLAGS_NO_REDUCTION | c4d.DRAWFLAGS_STATICBREAK)

def iter_container(container, callback=None, level=0):
    r"""
    Iterate over the passed *container* being a :class:`c4d.BaseContainer`
    instance recursively. The *callback* will be called for each key-value
    pair. The default callback will print out the values in the container.

    The *callback* is passed the containers key, value and stack-level.

    :Returns: None
    :Raises:  TypeError when *callback* is not callable.
    """

    if not callback:
        def callback(key, value, level):
            sys.stdout.write(level * '    ')
            print key,
            if isinstance(value, c4d.BaseContainer):
                print "Container:"
            else:
                print ":", value

    if not isinstance(callback, collections.Callable):
        raise TypeError('expected callback to be a callable instance.')

    for key, value in container:
        callback(key, value, level)
        if isinstance(value, c4d.BaseContainer):
            iter_container(value, callback, level + 1)

def current_state_to_object(op, container=c4d.BaseContainer()):
    r"""
    Makes the passed `c4d.BaseObject` instance an editable object by
    applieng a modeling command on it. The returned object's hierarchy
    will consist of Null-Objects and editable objects only.

    *container* is an argument assigned a new c4d.BaseContainer to
    optimize speed and memory usage, but you can pass your own
    c4d.BaseContainer in case you want to pass any additional
    information to the c4d.utils.SendModelingCommand function.

    Example code for the Script Manager:

    .. code-block:: python

        import c4dtools

        def main():
            obj = c4dtools.utils.current_state_to_object(op)
            doc.InsertObject(obj)
            c4d.EventAdd()

        main()

    Raises: TypeError if *op* is not a c4d.BaseObject instance.
    Returns: c4d.BaseObject
    """

    if not isinstance(op, c4d.BaseObject):
        raise TypeError('expected c4d.BaseObject, got %s.' %
                        op.__class__.__name__)

    doc = op.GetDocument()

    if not doc:
        csto_doc = c4d.documents.BaseDocument()
        csto_doc.InsertObject(op)
    else:
        csto_doc = doc

    result = c4d.utils.SendModelingCommand(
        c4d.MCOMMAND_CURRENTSTATETOOBJECT, [op], c4d.MODELINGCOMMANDMODE_ALL,
        container, csto_doc)[0]

    if not doc:
        op.Remove()

    return result

def join_polygon_objects(objects, dest_mat=None):
    r"""
    New in 1.2.8.
    This function creates one polygon object from the passed list
    *objects* containing :class:`c4d.PolygonObject` instances. Any other
    type of object is ignored.

    The returned polygon-object is located at the global world
    center.

    # TODO: Add description for parameters.
    """

    # Filter all polygon-objects from the passed sequence.
    objects = filter(lambda x: x.CheckType(c4d.Opolygon), objects)
    if not objects:
        return None

    if dest_mat is None:
        dest_mat = objects[0].GetMg()

    # Merge points and polygons into single lists and collect
    # all tags.
    points = []
    polys = []
    tags = []
    for obj in objects:
        mg = obj.GetMg() * ~dest_mat

        point_offset = len(points)
        for poly in obj.GetAllPolygons():
            poly.a += point_offset
            poly.b += point_offset
            poly.c += point_offset
            poly.d += point_offset
            polys.append(poly)

        for point in obj.GetAllPoints():
            point = point * mg
            points.append(point)

        tags.extend(obj.GetTags())

    # No points, no luck.
    if not points:
        return None

    # Create a polygon-object from the points and polygons.
    object = c4d.PolygonObject(len(points), len(polys))
    object.SetAllPoints(points)
    for i, poly in enumerate(polys):
        object.SetPolygon(i, poly)

    # Tell the object about the change.
    object.Message(c4d.MSG_UPDATE)

    # Create a list of unique tags for the object.
    new_tags = []
    for tag in tags:
        # Skip variable tags as they do not match the new
        # number of datasets anymore.
        if tag.CheckType(c4d.Tvariable):
            continue

        # Check if such a tag already exists.
        exists = False
        for ex_tag in new_tags:
            if ex_tag.CheckType(tag.GetType()):
                exists = ex_tag.GetDataInstance() == tag.GetDataInstance()
                if exists:
                    break

        if not exists:
            new_tags.append(tag.GetClone(c4d.COPYFLAGS_0))

    for tag in new_tags:
        object.InsertTag(tag)

    object.SetMg(dest_mat)
    return object

def serial_info():
    r"""
    New in 1.2.7.

    Returns serial-information of the user. Returns ``(sinfo, is_multi)``.
    *is_multi* indicates whether the *sinfo* is a multilicense information
    or not.
    """

    is_multi = True
    sinfo = c4d.GeGetSerialInfo(c4d.SERIALINFO_MULTILICENSE)
    if not sinfo['nr']:
        is_multi = False
        sinfo = c4d.GeGetSerialInfo(c4d.SERIALINFO_CINEMA4D)
    return sinfo, is_multi

def get_shader_bitmap(shader, irs=None):
    r"""
    A bitmap can be retrieved from a :class:`c4d.BaseShader` instance of
    type ``Xbitmap`` using its :meth:`~c4d.BaseShader.GetBitmap` method.
    This method must however be wrapped in calls to
    :func:`~c4d.BaseShader.InitRender` and :func:`~c4d.BaseShader.FreeRender`.

    This function initializes rendering of the passed *shader*, retrieves
    the bitmap and frees it.

    :Return: :class:`c4d.BaseBitmap` or ``None``.
    """
    if not irs:
        irs = render.InitRenderStruct()
    if shader.InitRender(irs) != c4d.INITRENDERRESULT_OK:
        return None

    bitmap = shader.GetBitmap()
    shader.FreeRender()
    return bitmap

def get_material_objects(doc):
    r"""
    New in 1.2.6.

    This function goes through the complete object hierarchy of the
    passed :class:`c4d.BaseDocument` and all materials with the objects
    that carry a texture-tag with that material. The returnvalue is an
    :class:`AtomDict` instance. The keys of the dictionary-like object
    are the materials in the document, their associated values are lists
    of :class:`c4d.BaseObject`. Note that an object *can* occure twice in
    the same list when the object has two tags with the same material on
    it.

    :param doc: :class:`c4d.BaseDocument`
    :return: :class:`AtomDict`
    """

    data = AtomDict()

    def callback(op):
        for tag in op.GetTags():
            if tag.CheckType(c4d.Ttexture):
                mat = tag[c4d.TEXTURETAG_MATERIAL]
                if not mat: continue

                data.setdefault(mat, []).append(op)

        for child in op.GetChildren():
            callback(child)

    for obj in doc.GetObjects():
        callback(obj)

    return data

def bl_iterator(obj, safe=False):
    r"""
    New in 1.2.8. Yields the passed object and all following objects
    in the hierarchy (retrieved via :func:`~c4d.BaseList2D.GetNext`). When
    the *safe* parameter is True, the next object will be retrieved before
    yielding to allow the yielded object to be moved in the hierarchy and
    iteration continues as if the object was not moved in hierarchy.
    """

    if safe:
        while obj:
            next = obj.GetNext()
            yield obj
            obj = next
    else:
        while obj:
            yield obj
            obj = obj.GetNext()

# =============================================================================
#                                Utility classes
# =============================================================================

class AtomDict(object):
    r"""
    New in 1.2.6.

    This class implements a subset of the dictionary interface but without the
    requirement of the :func:`__hash__` method to be implemented. It is using
    comparing objects directly with the ``==`` operator instead.
    """

    def __init__(self):
        super(AtomDict, self).__init__()
        self.__data = []

    def __getitem__(self, x):
        self.__get_item(x)[1]

    def __setitem__(self, x, v):
        try:
            self.__get_item(x)[1] = v
        except KeyError:
            self.__data.append([x, v])

    def __iter__(self):
        return self.iterkeys()

    def __repr__(self):
        content = ', '.join('%r: %r' % (k, v) for (k, v) in self.__data)
        return 'AtomDict({%s})' % content

    def __contains__(self, key):
        try:
            self.__get_item(key)
            return True
        except KeyError:
            return False

    def __get_item(self, x):
        for item in self.__data:
            if item[0] == x:
                return item
        raise KeyError(x)

    def setdefault(self, x, v):
        try:
            item = self.__get_item(x)
        except KeyError:
            item = [x, v]
            self.__data.append(item)
        return item[1]

    def keys(self):
        return list(self.iterkeys())

    def values(self):
        return list(self.itervalues())

    def items(self):
        return list(self.iteritems())

    def iterkeys(self):
        for key, value in self.__data:
            yield key

    def itervalues(self):
        for key, value in self.__data:
            yield value

    def iteritems(self):
        for key, value in self.__data:
            yield (key, value)

    def get(self, key, default=None):
        try:
            return self.__get_item(key)[1]
        except KeyError:
            return default

    def set(self, key, value):
        self.__setitem__(key, value)

    def pop(self, key, *args):
        try:
            item = self.__get_item(key)
            self.__data.remove(item)
            return item[1]
        except KeyError:
            if not args:
                raise
            else:
                return args[0]

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
    """

    def __init__(self, high_priority=False, use_sys_path=True):
        super(Importer, self).__init__()
        self.path = []
        self.use_sys_path = use_sys_path
        self.high_priority = high_priority

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

        prev_path = sys.path
        if self.use_sys_path:
            if self.high_priority:
                sys.path = self.path + sys.path
            else:
                sys.path = sys.path + self.path

        prev_modules = sys.modules.copy()

        # Remove any existing modules with the passed name from
        # sys.modules.
        for k in sys.modules.keys():
            if k == name or k.startswith('%s.' % name):
                del sys.modules[k]

        try:
            m = __import__(name)
            for n in name.split('.')[1:]:
                m = getattr(m, n)
            return m
        except:
            raise
        finally:
            sys.path = prev_path

            # Restore the old module configuration. Only modules that have
            # not been in sys.path before will be removed.
            for k, v in sys.modules.items():
                if k not in prev_modules and self.is_local(v) or not v:
                    del sys.modules[k]
                else:
                    sys.modules[k] = v

class Watch(object):
    r"""
    Utility class for measuring execution-time of code-blocks
    implementing the with-interface.

        >>> with Watch() as w:
        ...     time_intensive_code()
        ...
        >>> w.delta
        4.32521002
    """

    def __init__(self):
        super(Watch, self).__init__()
        self.reset()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        self.stop()

    def _watch_not_started(self, action):
        raise RuntimeError('Watch must be started before action "%s".' %
                           action)

    def start(self):
        r"""
        Start the time measuring.
        """

        self._start = time.time()
        self._stop = -1

    def stop(self):
        r"""
        Stop the time measuring.

        :Raises: :class:`RuntimeError` when :func:`Watch.start` was not
                 called before.
        """

        if self._start < 0:
            self._watch_not_started('stop')

        self._stop = time.time()

    def reset(self):
        r"""
        Reset the information and return the Watch into a state where
        time measuring has not been started yet.
        """

        self._start = -1
        self._stop = -1

    @property
    def delta(self):
        r"""
        Returns the difference between the time Watch.start() has been
        and Watch.stop() has been called. If Watch.stop() has not yet
        been invoked, the current time is used.

        Raises: RuntimeError when Watch.start() has not been called
                before.
        """

        if self._start < 0:
            self._watch_not_started('delta')

        if self._stop < 0:
            stop = time.time()
        else:
            stop = self._stop

        return stop - self._start

    @property
    def started(self):
        r"""
        Returns True when the Watch has been started.
        """

        return self._start >= 0

    @property
    def stopped(self):
        r"""
        Returns True when the Watch has been stopped.
        """

        return self._stop >= 0

class FileChangedChecker(object):
    r"""
    This class keeps track of a file on the local filesystem and tell
    you if the specific file has changed since the last time the
    FileChangedChecker was asked this question.

    It can run in two modes: pushing or pulling. With pulling, we mean
    to request the information whether the file has changed or not.
    With pushing, we mean to get notified when the file has changed.
    Pushing comes in connection with threading. Only one thread can be
    run from on FileChangedChecker instance.

    Example for pulling:

    .. code-block:: python

        f = FileChangedChecker(my_filename)
        # ...
        if f.has_changed():
            print ("File %s has changed since `f` has been created." %
                   f.filename)

    Example for pushing:

    .. code-block:: python

        f = FileChangedChecker(my_filename)
        def worker(f):
            print ("File %s has changed since `f` has been created." %
                   f.filename)
        f.run_in_background(worker)
    """

    class Worker(threading.Thread):
        r"""
        This is the worker class instantiated by the FileChangedChecker
        to run in the background.
        """

        def __init__(self, checker, callback, period):
            super(FileChangedChecker.Worker, self).__init__()
            self.checker = checker
            self.callback = callback
            self.period = period
            self.running = False
            self.terminated = True

        # threading.Thread

        def run(self):
            self.running = True
            self.terminated = False

            while self.running:
                if self.checker.has_changed():
                    self.callback(self.checker)

                time.sleep(self.period)

            self.terminated = True
            self.checker.worker_ended(self)

    def __init__(self, filename):
        r"""
        Initialize the instance with a valid filename.

        Raises: OSError if the passed filename does not point to a
                valid file on the local filesystem.
        """
        super(FileChangedChecker, self).__init__()
        self.filename = filename
        self.last_time = os.path.getmtime(self.filename)
        self.active_worker = None
        self.disposing_workers = []

    def __del__(self):
        if self.active_worker:
            self.stop_background()

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, filename):
        if not os.path.isfile(filename):
            msg = 'the passed filename does not point to an existing file.'
            raise OSError(msg)

        self._filename = filename

    def has_changed(self):
        r"""
        This method returns True when file pointed to by the stored
        filename has changed since the last time the FileChangedChecker
        was asked for.

        Note: When the file has not changed since the initialization
              of the FileChangedChecker instance, this method will
              return False (i.e. the first call to this function will
              tell you the file has *not* changed).
        """

        new_time = os.path.getmtime(self.filename)
        if new_time > self.last_time:
            self.last_time = new_time
            return True

        return False

    def run_in_background(self, callback, period=0.5):
        r"""
        Start a new thread invoking the callable *callback* passing
        the FileChangedChecker instance when the file it points to
        has changed. *period* defines the time in seconds that passes
        until the next time the thread checks for the change.

        Raises: RuntimeError when a thread is still running for this
                instance.
        """

        if self.active_worker:
            raise RuntimeError('cannot start multiple threads for '
                               'FileChangedChecker instance.')

        worker = FileChangedChecker.Worker(self, callback, period)
        worker.start()
        self.active_worker = worker

    def stop_background(self, join=False):
        r"""
        Stops the background operation started with
        ``run_in_background()``. When *join* evaluates to True, this
        method will wait until the thread has stopped working before
        terminating.

        Raises: RuntimeError when no thread has been started yet.
        """

        if not self.active_worker:
            raise RuntimeError('no running thread to stop.')

        self.disposing_workers.append(self.active_worker)
        self.active_worker.running = False
        self.active_worker = None

    def worker_ended(self, worker):
        r"""
        Not public. This method is called by a FileChangedChecker.Worker
        instance to dispose the worker from the list of not yet
        disposed workers.

        Raises: RuntimeError if *worker* is not in the list of not yet
                disposed workers.
                TypeError if *worker* is not an instance of
                FileChangedChecker.Worker.
        """

        if not isinstance(worker, FileChangedChecker.Worker):
            raise TypeError('expected FileChangedChecker.Worker instance.')

        if not worker in self.disposing_workers:
            raise RuntimeError('worker not found, could not be removed.')

        self.disposing_workers.remove(worker)

class Filename(object):
    r"""
    A wrapper class for the os.path module.
    """

    def __init__(self, filename):
        super(Filename, self).__init__()
        self.filename = os.path.normpath(filename)

    def __repr__(self):
        return 'Filename("%s")' % self.filename

    def __str__(self):
        return self.filename

    def __add__(self, other):
        if isinstance(other, Filename):
            other = other.filename
        return self.join(self.filename, other)

    def __radd__(self, other):
        if isinstance(other, Filename):
            other = other.filename
        return self.new_instance(other).join(self.filename)

    def __eq__(self, other):
        if isinstance(other, Filename):
            other = other.filename
        return os.path.samefile(self.filename, other)

    def new_instance(self, filename):
        return Filename(filename)

    def join(self, *parts):
        return self.new_instance(os.path.join(self.filename, *parts))

    def dirname(self):
        return self.new_instance(os.path.dirname(self.filename))

    def split(self):
        a, b = os.path.split(self.filename)
        return (self.new_instance(a), self.new_instance(b))

    def splitdrive(self):
        a, b = os.path.splitdrive(self.filename)
        return (self.new_instance(a), self.new_instance(b))

    def basename(self):
        return self.new_instance(os.path.basename(self.filename))

    def exists(self):
        return os.path.exists(self.filename)

    def lexists(self):
        return os.path.lexists(self.filename)

    def isfile(self):
        return os.path.isfile(self.filename)

    def isdir(self):
        return os.path.isdir(self.filename)

    def isabs(self):
        return os.path.isabs(self.filename)

    def islink(self):
        return os.path.islink(self.filename)

    def ismount(self):
        return os.path.ismount(self.filename)

    def suffix(self, new_suffix=None):
        r"""
        Called with no arguments, this method returns the suffix of the
        filename. When passing a string, the suffix will be exchanged
        to the passed suffix.

        Raises: TypeError when *new_suffix* is not None and not a string.
        """

        if new_suffix:
            if not isinstance(new_suffix, basestring):
                raise TypeError('expected str, got %s.' % clsname(new_suffix))

            self.filename = change_suffix(self.filename, new_suffix)
        else:
            index = self.filename.rfind('.')
            if index < 0:
                return ''
            else:
                return self.filename[index + 1:]

    def getatime(self):
        return os.path.getatime(self.filename)

    def getmtime(self):
        return os.path.getmtime(self.filename)

    def getctime(self):
        return os.path.getctime(self.filename)

    def getsize(self):
        return os.path.getsize(self.filename)

    def iglob(self, *glob_exts):
        r"""
        Returns a generator yielding all filenames that were found
        by globbing the filename joined with the passed *\*glob_exts*.
        """

        for ext in glob_exts:
            for filename in glob.iglob(os.path.join(self.filename, ext)):
                yield filename

class PolygonObjectInfo(object):
    r"""
    New in 1.2.5.

    This class stores the points and polygons of a polygon-object and
    additionally computes it's normals and polygon-midpoints.
    """

    def __init__(self):
        super(PolygonObjectInfo, self).__init__()
        self.points = []
        self.polygons = []
        self.normals = []
        self.midpoints = []
        self.pointcount = 0
        self.polycount = 0

    def init(self, op):
        r"""
        Initialize the instance. *op* must be a :class:`c4d.PolygonObject`
        instance.
        """

        ensure_type(op, c4d.PolygonObject)

        points = op.GetAllPoints()
        polygons = op.GetAllPolygons()
        normals = []
        midpoints = []

        for p in polygons:
            a, b, c, d = points[p.a], points[p.b], points[p.c], points[p.d]

            # Compute the polygon's normal vector.
            normal = (a - b).Cross(a - d)
            normal.Normalize()

            # Compute the mid-point of the polygon.
            midpoint = a + b + c
            if p.c == p.d:
                midpoint *= 1.0 / 3
            else:
                midpoint += d
                midpoint *= 1.0 / 4

            normals.append(normal)
            midpoints.append(midpoint)

        self.points = points
        self.polygons = polygons
        self.normals = normals
        self.midpoints = midpoints
        self.pointcount = len(points)
        self.polycount = len(polygons)


