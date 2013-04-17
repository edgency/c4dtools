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
c4dtools.decorators
~~~~~~~~~~~~~~~~~~~

*New in 1.2.9*. Implements usefuly decorator functions and classes.
"""

import collections

def f_attrs(self=False, **attrs):
    r"""
    - *New in 1.2.6*.
    - *Changed in 1.2.9*
        - Moved from ``utils`` to ``decorators``
        - Added *self* parameter.
    This function returns a decorator adding all passed keyword arguments
    as attributes to the decorated function. If the parameter *self* is
    given True, the function object itself will be passed as first argument
    to the function.

    .. code-block:: python

        @f_attrs(attr='value here')
        def func1(arg):
            print func1.attr
            return arg ** 2

        @f_attrs(True, attr='value here')
        def func2(self, arg):
            print self.attr
            return arg ** 2
    """

    def wrapper(func):
        for k, v in attrs.iteritems():
            setattr(func, k, v)
        if self:
            f_save = func
            def func(*args, **kwargs):
                return f_save(f_save, *args, **kwargs)
        return func

    return wrapper

def override(fnc=None):
    r"""
    *New in 1.2.9*. Decorator for class-methods. Use in combination with
    the :func:`subclass` decorator.

    This decorator will raise a :class:`NotImplementedError`
    when the decorated function does not override a method implemented
    in one of the base classes.


    Call without arguments before decorating to prevent the checking and
    use it as code annotation only.
    """

    if fnc is None:
        return lambda x: x
    else:
        return _Override(fnc)

def subclass(cls):
    r"""
    A class decorator checking each :class:`override` decorated
    function. Use it as follows:

    .. code-block:: python

        @subclass
        class Subclass(Superclass):

            @override
            def overriden_function(self):
                # ...
                pass

    """

    for key in dir(cls):
        value = getattr(cls, key)
        if isinstance(value, _Override):
            value.check(cls)
            setattr(cls, key, value.func)

    return cls


class _Override(object):

    def __init__(self, func):
        super(_Override, self).__init__()
        self.func = func
        self.__name__ = getattr(func, '__name__', None)
        self.func_name = func.func_name

    def check(self, cls):
        for base in cls.__bases__:
            has = hasattr(base, self.func_name)
            func = getattr(base, self.func_name, None)
            if has and isinstance(func, collections.Callable):
                return

        raise NotImplementedError('No baseclass of %s '
                'implements a method %s()' % (cls.__name__, self.func_name))



