# coding: utf-8
#
# Copyright (C) 2012, Niklas Rosenstein

import c4d

class Command(c4d.plugins.CommandData):
    r"""
    This class is wrapping the CommandData class to make the
    registration of plugins of this kind easier. Subclasses are
    automatically registered on `c4dtools.plugins.main()` unless
    `autoregister` evaluates to False.

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
    autoregister = True

    PLUGIN_INFO = c4d.PLUGINFLAG_COMMAND_HOTKEY
    PLUGIN_ICON = None

    def register(self):
        r"""
        This method registers the plugin to Cinema 4D by using the data
        set in the instances attributes. See the class-documentation
        for more information.
        """

        if self.PLUGIN_ICON:
            if not isinstance(self.PLUGIN_ICON, c4d.bitmaps.BaseBitmap):
                icon = c4d.bitmaps.BaseBitmap()
                icon.InitWith(self.PLUGIN_ICON)
            else:
                icon = self.PLUGIN_ICON
        else:
            icon = None

        result = c4d.plugins.RegisterCommandPlugin(
            self.PLUGIN_ID, self.PLUGIN_NAME, self.PLUGIN_INFO, icon,
            self.PLUGIN_HELP, self)

        if result:
            self.__class__.is_registered = True
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
