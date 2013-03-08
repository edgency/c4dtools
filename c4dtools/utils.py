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

# Path operations

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

# Vector operations

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

# Several utilities

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

# Cinema 4D related stuff, making common things easy

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

# Utility classes

class Importer(object):
    r"""
    Use this class to enable importing modules from specific
    directories independent from ``sys.path``.

    .. attribute:: high_priority
        When this value evaluates to ``True``, the paths defined in the
        imported are preprended to the original paths in ``sys.path``.
        The're appended otherwise. Does not have effect when
        :attr:`use_sys_path` evaluates to ``True``.

    .. attribute:: use_sys_path
        When this value is ``True``, the original paths from ``sys.path``
        are used additionally to the paths defined in the imported.
    """

    def __init__(self, high_priority=False, use_sys_path=True):
        super(Importer, self).__init__()
        self.path = []
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
            new_paths.append(path)

        self.path.extend(new_paths)

    def import_(self, name, load_globally=False):
        r"""
        Import the module with the given name from the directories
        added to the Importer. The loaded module will not be inserted
        into `sys.modules` unless ``load_globall`` is True.
        """

        prev_path = sys.path
        if self.use_sys_path:
            if self.high_priority:
                sys.path = self.path + sys.path
            else:
                sys.path = sys.path + self.path

        prev_module = None
        if name in sys.modules and not load_globally:
            prev_module = sys.modules[name]
            del sys.modules[name]

        try:
            m = __import__(name)
            for n in name.split('.')[1:]:
                m = getattr(m, n)
            return m
        except:
            raise
        finally:
            sys.path = prev_path

            # Restore the old module or remove the module that was just
            # loaded from ``sys.modules`` only if we do not load the module
            # globally.
            if not load_globally:
                if prev_module:
                    sys.modules[name] = prev_module
                else:
                    if name in sys.modules:
                        del sys.modules[name]

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
