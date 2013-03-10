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
c4dtools.resource.menuparser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements parsing a Menu-resource in order to attach the
resource to a dialog. It requires the py-scan module in version 0.4.2 or
higher.
"""

import c4d
import scan
import string

from c4dtools.resource import Resource

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

class MenuNode(object):

    def _assert_symbol(self, symbol, res):
        if not res.has_symbol(symbol):
            raise AttributeError('Resource does not have required symbol %r' %
                                 symbol)

    def render(self, dialog, res):
        pass

class MenuContainer(MenuNode):

    def __init__(self, symbol):
        super(MenuContainer, self).__init__()
        self.children = []
        self.symbol = symbol

    def add(self, child):
        self.children.append(child)

    def render(self, dialog, res):
        self._assert_symbol(self.symbol, res)
        dialog.MenuSubBegin(res.string.get(self.symbol)())
        try:
            for child in self.children:
                child.render(dialog, res)
        finally:
            dialog.MenuFinished()

class MenuSeperator(MenuNode):

    def render(self, dialog, res):
        dialog.MenuAddSeparator()

class MenuCommand(MenuNode):

    def __init__(self, command_id=None, symbol=None):
        super(MenuCommand, self).__init__()
        assert command_id or symbol
        self.command_id = command_id
        self.symbol = symbol

    def render(self, dialog, res):
        command_id = self.command_id
        if not command_id:
            self._assert_symbol(self.symbol, res)
            command_id = res.get(self.symbol)

        dialog.MenuAddCommand(command_id)

class MenuString(MenuNode):

    def __init__(self, symbol):
        super(MenuString, self).__init__()
        self.symbol = symbol

    def render(self, dialog, res):
        self._assert_symbol(self.symbol, res)
        dialog.MenuAddString(*res.string.get(self.symbol).both)

class MenuSet(scan.TokenSet):

    def on_init(self):
        digits = string.digits
        letters = string.letters + '_'

        self.add('comment', 2, scan.HashComment(skip=True))
        self.add('menu',    1, scan.Keyword('MENU'))
        self.add('command', 1, scan.Keyword('COMMAND'))
        self.add('bopen',   1, scan.Keyword('{'))
        self.add('bclose',  1, scan.Keyword('}'))
        self.add('end',     1, scan.Keyword(';'))
        self.add('sep',     0, scan.CharacterSet('-'))
        self.add('symbol',  0, scan.CharacterSet(letters, letters + digits))
        self.add('number',  0, scan.CharacterSet(digits))

class MenuParser(object):

    def __init__(self, **options):
        super(MenuParser, self).__init__()
        self.options = options

    def __getitem__(self, name):
        return self.options[name]

    def _assert_type(self, token, *tokentypes):
        for tokentype in tokentypes:
            if not token or token.type != tokentype:
                raise scan.UnexpectedTokenError(token, tokentypes)

    def _command(self, lexer):
        self._assert_type(lexer.token, lexer.t_command)
        lexer.read_token()

        command_id = None
        symbol_name = None
        if lexer.token.type == lexer.t_number:
            command_id = int(lexer.token.value)
        elif lexer.token.type == lexer.t_symbol:
            symbol_name = lexer.token.value
        else:
            raise scan.UnexpectedTokenError(lexer.token, [lexer.t_number,
                    lexer.t_symbol])

        return MenuCommand(command_id, symbol_name)

    def _menu(self, lexer):
        self._assert_type(lexer.token, lexer.t_menu)
        lexer.read_token()
        self._assert_type(lexer.token, lexer.t_symbol)
        items = MenuContainer(lexer.token.value)
        lexer.read_token()
        self._assert_type(lexer.token, lexer.t_bopen)
        lexer.read_token()

        while lexer.token and lexer.token.type != lexer.t_bclose:
            require_endstmt = True
            if lexer.token.type == lexer.t_menu:
                item = self._menu(lexer)
                require_endstmt = False
            elif lexer.token.type == lexer.t_command:
                item = self._command(lexer)
            elif lexer.token.type == lexer.t_sep:
                item = MenuSeperator()
            elif lexer.token.type == lexer.t_symbol:
                item = MenuString(lexer.token.value)
            else:
                raise scan.UnexpectedTokenError(lexer.token, [lexer.t_menu,
                        lexer.t_command, lexer.t_sep, lexer.t_symbol])

            items.add(item)

            if require_endstmt:
                lexer.read_token()
                self._assert_type(lexer.token, lexer.t_end)
                lexer.read_token()

        self._assert_type(lexer.token, lexer.t_bclose)
        lexer.read_token()
        return items

    def parse(self, lexer):
        menus = []
        while lexer.token:
            menu = self._menu(lexer)
            menus.append(menu)
        return menus


def parse_file(filename):
    r"""
    Parse a ``*.menu`` file from the local file-system. Returns a list
    of :class:`MenuContainer` objects.
    """

    fl = open(filename)
    return parse_fileobject(fl)

def parse_string(data):
    r"""
    Parse a ``*.menu`` formatted string. Returns a list of of
    :class:`MenuContainer` objects.
    """

    fl = StringIO.StringIO(data)
    fl.seek(0)
    return parse_fileobject(fl)

def parse_fileobject(fl):
    r"""
    Parse a file-like object. Returns a list of :class:`MenuContainer`
    objects.
    """

    scanner = scan.Scanner(fl)
    scanner.read()
    lexer = scan.Lexer(scanner, MenuSet())
    lexer.read_token()
    parser = MenuParser()
    return parser.parse(lexer)

def parse_and_prepare(filename, dialog, res):
    r"""
    Like :func:`parse_file`, but renders the parsed menus to the dialog.
    """

    if not isinstance(dialog, c4d.GeDialog):
        raise TypeError('Expected c4d.gui.GeDialog as 2nd argument.')
    if not isinstance(res, Resource):
        raise TypeError('Expected c4dtools.resource.Resource as 3rd argument.')

    menus = parse_file(filename)
    for menu in menus:
        menu.render(dialog, res)




