from nodes.node_implementations.animator import AnimatorNode
from nodes.node_implementations.canvas import CanvasNode
from nodes.node_implementations.colour_filler import ColourFillerNode
from nodes.node_implementations.colour_list import ColourListNode
from nodes.node_implementations.colours import FillNode
from nodes.node_implementations.drawing_cropper import DrawingCropperNode
from nodes.node_implementations.drawing_group import DrawingGroupNode
from nodes.node_implementations.drawing_group_subset import DrawingGroupSubsetNode
from nodes.node_implementations.ellipse_sampler import EllipseSamplerNode
from nodes.node_implementations.function import FunctionNode
from nodes.node_implementations.function_sampler import FunSamplerNode
from nodes.node_implementations.grid import GridNode
from nodes.node_implementations.iterator import IteratorNode
from nodes.node_implementations.overlay import OverlayNode
from nodes.node_implementations.port_forwarder import PortForwarderNode
from nodes.node_implementations.random_iterator import RandomIteratorNode
from nodes.node_implementations.random_list_selector import RandomListSelectorNode
from nodes.node_implementations.random_port_selector import RandomPortSelectorNode
from nodes.node_implementations.shape_repeater import ShapeRepeaterNode
from nodes.node_implementations.shapes import ShapeNode
from nodes.node_implementations.stacker import StackerNode
from nodes.node_implementations.warp import WarpNode

node_classes = [
    GridNode,
    ShapeNode,
    CanvasNode,
    ShapeRepeaterNode,
    FunctionNode,
    WarpNode,
    FunSamplerNode,
    IteratorNode,
    FillNode,
    ColourFillerNode,
    ColourListNode,
    OverlayNode,
    RandomPortSelectorNode,
    RandomListSelectorNode,
    RandomIteratorNode,
    StackerNode,
    DrawingGroupNode,
    DrawingGroupSubsetNode,
    PortForwarderNode,
    EllipseSamplerNode,
    DrawingCropperNode,
    AnimatorNode
]
