# from ui.nodes.node_implementations.blaze_maker import BlazeMakerNode
# from ui.nodes.node_implementations.canvas import CanvasNode
# from ui.nodes.node_implementations.colour import ColourNode
# from ui.nodes.node_implementations.colour_filler import ColourFillerNode
# from ui.nodes.node_implementations.colour_list import ColourListNode
# from ui.nodes.node_implementations.drawing_group import DrawingGroupNode
# from ui.nodes.node_implementations.ellipse_sampler import EllipseSamplerNode
# from ui.nodes.node_implementations.function import FunctionNode
# from ui.nodes.node_implementations.function_sampler import FunSamplerNode
# from ui.nodes.node_implementations.gradient import GradientNode
from ui.nodes.node_implementations.canvas import CanvasNode
from ui.nodes.node_implementations.colour import ColourNode
from ui.nodes.node_implementations.colour_filler import ColourFillerNode
from ui.nodes.node_implementations.colour_list import ColourListNode
from ui.nodes.node_implementations.drawing_group import DrawingGroupNode
from ui.nodes.node_implementations.function import FunctionNode
from ui.nodes.node_implementations.function_sampler import FunSamplerNode
from ui.nodes.node_implementations.gradient import GradientNode
from ui.nodes.node_implementations.grid import GridNode
from ui.nodes.node_implementations.iterator import IteratorNode
from ui.nodes.node_implementations.overlay import OverlayNode
from ui.nodes.node_implementations.random_iterator import RandomIteratorNode
from ui.nodes.node_implementations.random_list_selector import RandomListSelectorNode
from ui.nodes.node_implementations.shape_repeater import ShapeRepeaterNode
from ui.nodes.node_implementations.shapes import ShapeNode
from ui.nodes.node_implementations.stacker import StackerNode
from ui.nodes.node_implementations.warp import WarpNode


# from ui.nodes.node_implementations.iterator import IteratorNode
# from ui.nodes.node_implementations.overlay import OverlayNode
# from ui.nodes.node_implementations.port_forwarder import PortForwarderNode
# from ui.nodes.node_implementations.random_iterator import RandomIteratorNode
# from ui.nodes.node_implementations.random_list_selector import RandomListSelectorNode
# from ui.nodes.node_implementations.shapes import ShapeNode
# from ui.nodes.node_implementations.shape_repeater import ShapeRepeaterNode
# from ui.nodes.node_implementations.stacker import StackerNode
# from ui.nodes.node_implementations.warp import WarpNode


class NodeSettings:
    def __init__(self, resizable=True):
        self.resizable = resizable


# node_settings = [
#     (EllipseSamplerNode, NodeSettings()),
#     (BlazeMakerNode, NodeSettings()),
#     (PortForwarderNode, NodeSettings()),
# ]
node_settings = [(GridNode, NodeSettings()),
                 (ShapeNode, NodeSettings()),
                 (CanvasNode, NodeSettings(resizable=False)),
                 (ShapeRepeaterNode, NodeSettings()),
                 (FunctionNode, NodeSettings()),
                 (WarpNode, NodeSettings()),
                 (FunSamplerNode, NodeSettings()),
                 (IteratorNode, NodeSettings()),
                 (ColourNode, NodeSettings()),
                 (ColourFillerNode, NodeSettings()),
                 (ColourListNode, NodeSettings()),
                 (GradientNode, NodeSettings()),
                 (OverlayNode, NodeSettings()),
                 (RandomListSelectorNode, NodeSettings()),
                 (RandomIteratorNode, NodeSettings()),
                 (StackerNode, NodeSettings()),
                 (DrawingGroupNode, NodeSettings())]


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
