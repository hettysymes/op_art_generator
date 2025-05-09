# node_classes = [GridNode, ShapeNode, ShapeRepeaterNode, CheckerboardNode, WarpNode,
#                 FunctionNode, CanvasNode, IteratorNode, ColourListNode, FunSamplerNode, ColourFillerNode, OverlayNode,
#                 GradientNode, IteratorSelectorNode, EllipseSamplerNode, BlazeMakerNode, StackerNode, ColourNode,
#                 RandomColourSelectorNode, DrawingGroupNode]
from enum import Enum, auto

from ui.nodes.node_implementations.canvas import CanvasNode
from ui.nodes.node_implementations.colour import ColourNode
from ui.nodes.node_implementations.gradient import GradientNode
from ui.nodes.node_implementations.grid import GridNode
from ui.nodes.node_implementations.shape import PolygonNode, RectangleNode, ShapeNode
from ui.nodes.node_implementations.shape_repeater import ShapeRepeaterNode


class NodeSettings:
    def __init__(self, resizable=True):
        self.resizable = resizable

node_settings = [(ShapeNode, NodeSettings()),
                 (GridNode, NodeSettings()),
                 (CanvasNode, NodeSettings(resizable=False)),
                 (ShapeRepeaterNode, NodeSettings()),
                 (ColourNode, NodeSettings()),
                 (GradientNode, NodeSettings())]

def node_classes():
    node_classes = []
    for node_setting in node_settings:
        node = node_setting[0]
        node_classes.append(node)
    return node_classes

def node_setting(name):
    for node_setting in node_settings:
        node, setting = node_setting
        if node.name() == name:
            return setting
    raise KeyError("Node setting not found for given node name.")