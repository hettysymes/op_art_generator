from ui.nodes.node_implementations.blaze_maker import BlazeMakerNode
from ui.nodes.node_implementations.canvas import CanvasNode
from ui.nodes.node_implementations.colour import ColourNode
from ui.nodes.node_implementations.colour_filler import ColourFillerNode
from ui.nodes.node_implementations.colour_list import ColourListNode
from ui.nodes.node_implementations.drawing_group import DrawingGroupNode
from ui.nodes.node_implementations.ellipse_sampler import EllipseSamplerNode
from ui.nodes.node_implementations.function import FunctionNode
from ui.nodes.node_implementations.function_sampler import FunSamplerNode
from ui.nodes.node_implementations.gradient import GradientNode
from ui.nodes.node_implementations.grid import GridNode
from ui.nodes.node_implementations.iterator import IteratorNode
from ui.nodes.node_implementations.overlay import OverlayNode
from ui.nodes.node_implementations.port_forwarder import PortForwarderNode
from ui.nodes.node_implementations.random_list_selector import RandomListSelectorNode
from ui.nodes.node_implementations.shape import ShapeNode
from ui.nodes.node_implementations.shape_repeater import ShapeRepeaterNode
from ui.nodes.node_implementations.stacker import StackerNode
from ui.nodes.node_implementations.warp import WarpNode


class NodeSettings:
    def __init__(self, resizable=True):
        self.resizable = resizable


node_settings = [
    (GridNode, NodeSettings()),
    (ShapeNode, NodeSettings()),
    (ShapeRepeaterNode, NodeSettings()),
    (WarpNode, NodeSettings()),
    (FunctionNode, NodeSettings()),
    (CanvasNode, NodeSettings(resizable=False)),
    (IteratorNode, NodeSettings()),
    (ColourListNode, NodeSettings()),
    (FunSamplerNode, NodeSettings()),
    (ColourFillerNode, NodeSettings()),
    (OverlayNode, NodeSettings()),
    (GradientNode, NodeSettings()),
    (EllipseSamplerNode, NodeSettings()),
    (BlazeMakerNode, NodeSettings()),
    (StackerNode, NodeSettings()),
    (ColourNode, NodeSettings()),
    (RandomListSelectorNode, NodeSettings()),
    (DrawingGroupNode, NodeSettings()),
    (PortForwarderNode, NodeSettings())
]


def node_classes():
    node_classes = []
    for node_setting in node_settings:
        node = node_setting[0]
        node_classes.append(node)
    return node_classes


def node_setting(name):
    if name == "Custom":
        return NodeSettings()
    for node_setting in node_settings:
        node, setting = node_setting
        if node.name() == name:
            return setting
    raise KeyError("Node setting not found for given node name.")
