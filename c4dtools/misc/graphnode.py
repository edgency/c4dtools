# coding: utf-8
#
# Copyright (C) 2012, Niklas Rosenstein

import c4d
from c4d.modules import graphview as gv
from c4dtools.utils import vbbmid

class GraphNode(object):
    r"""
    This class is a thin wrapper for the `c4d.modules.graphview.GvNode`
    class providing an easy interface for accessing and modifieng the
    visual appeareance of an XPresso node in the XPresso editor.

    Currently, only accessing the position and size is supported.
    """

    POS_X = 100
    POS_Y = 101
    SIZE_X = 108
    SIZE_Y = 109

    def __init__(self, node):
        super(GraphNode, self).__init__()
        self.node = node

        container = node.GetDataInstance()
        container = self.get_graphcontainer(container)
        self.graphdata = container

    def get_graphcontainer(self, container):
        r"""
        This method returns the container containing the graphdata for
        the node in the XPresso grap based on the `GvNode`s container.
        """

        data = container.GetContainerInstance(1001)
        data = data.GetContainerInstance(1000)
        return data

    @property
    def position(self):
        data = self.graphdata
        return c4d.Vector(data.GetReal(self.POS_X), data.GetReal(self.POS_Y), 0)

    @position.setter
    def position(self, value):
        data = self.graphdata
        data.SetReal(self.POS_X, value.x)
        data.SetReal(self.POS_Y, value.y)

    @property
    def size(self):
        data = self.graphdata
        return c4d.Vector(data.GetReal(self.SIZE_X), data.GetReal(self.SIZE_Y), 0)

    @size.setter
    def size(self, value):
        data = self.graphdata
        data.SetReal(self.SIZE_X, value.x)
        data.SetReal(self.SIZE_Y, value.y)

def find_selected_nodes(root):
    r"""
    Finds the group of selected nodes in the XPresso Manager and returns
    a list of GvNode objects.
    """

    children = root.GetChildren()
    selected = []
    for child in children:
        if child.GetBit(c4d.BIT_ACTIVE):
            selected.append(child)
    if not selected:
        for child in children:
            selected = find_selected_nodes(child)
            if selected:
                return selected
    return selected

def find_nodes_mid(nodes):
    r"""
    Finds the mid-point of the passed list of
    `c4dtools.misc.graphnode.GraphNode` instances.
    """

    if not nodes:
        return c4d.Vector(0)

    vectors = [n.position for n in nodes]
    return vbbmid(vectors)


