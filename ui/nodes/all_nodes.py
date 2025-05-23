from ui.nodes.node_implementations.animator import AnimatorNode
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
from ui.nodes.node_implementations.random_iterator import RandomIteratorNode
from ui.nodes.node_implementations.random_list_selector import RandomListSelectorNode
from ui.nodes.node_implementations.shape_repeater import ShapeRepeaterNode
from ui.nodes.node_implementations.shapes import ShapeNode
from ui.nodes.node_implementations.stacker import StackerNode
from ui.nodes.node_implementations.warp import WarpNode

node_classes = [
    GridNode,
    ShapeNode,
    CanvasNode,
    ShapeRepeaterNode,
    FunctionNode,
    WarpNode,
    FunSamplerNode,
    IteratorNode,
    ColourNode,
    ColourFillerNode,
    ColourListNode,
    GradientNode,
    OverlayNode,
    RandomListSelectorNode,
    RandomIteratorNode,
    StackerNode,
    DrawingGroupNode,
    PortForwarderNode,
    EllipseSamplerNode,
    AnimatorNode
]
