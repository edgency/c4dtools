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
c4dtools.plugins
~~~~~~~~~~~~~~~~
"""

import os
import sys
import c4d

class Command(c4d.plugins.CommandData):
    r"""
    This class is wrapping the CommandData class to make the
    registration of plugins of this kind easier. Subclasses are
    automatically registered on ``c4dtools.plugins.main()`` unless
    ``autoregister`` evaluates to False.

    An instance of a subclass of this class must provide the following
    attributes to be successfully registered:

    - PLUGIN_ID
    - PLUGIN_NAME
    - PLUGIN_HELP
    - PLUGIN_INFO [optional]
    - PLUGIN_ICON [optional]
    """

    # This attribute is set from `c4dtools.plugins.main()`.
    detected = False
    is_registered = False
    tried_register = False
    registered_instance = None

    autoregister = True

    PLUGIN_INFO = c4d.PLUGINFLAG_COMMAND_HOTKEY
    PLUGIN_ICON = None

    def register(self):
        r"""
        This method registers the plugin to Cinema 4D by using the data
        set in the instances attributes. See the class-documentation
        for more information.
        """
        cls = self.__class__

        # Do not register if already tried or is already registered.
        if cls.tried_register:
            return self.is_registered

        if self.PLUGIN_ICON:
            if isinstance(self.PLUGIN_ICON, c4d.bitmaps.BaseBitmap):
                icon = self.PLUGIN_ICON
            else:
                icon = c4d.bitmaps.BaseBitmap()
                icon.InitWith(self.PLUGIN_ICON)
        else:
            icon = None

        cls.tried_register = True
        result = c4d.plugins.RegisterCommandPlugin(
            self.PLUGIN_ID, self.PLUGIN_NAME, self.PLUGIN_INFO, icon,
            self.PLUGIN_HELP, self)
        cls.is_registered = bool(result)
        if result:
            cls.is_registered = True
            cls.registered_instance = self
        return result

def gather_subclasses(clazz):
    r"""
    Returns a list of all subclasses that require to be registered.
    """

    classes = []

    for subclass in clazz.__subclasses__():
        classes.extend(gather_subclasses(subclass))
        if subclass.autoregister and not subclass.detected:
            classes.append(subclass)

    return classes

def main():
    r"""
    Gathers all subclasses of the plugin classes in this module and
    registers them to Cinema 4D unless `autoregister` evaluates to
    False.
    """

    for command_class in gather_subclasses(Command):
        command = command_class()
        command.register()


