from collections import defaultdict

from nodes.node_defs import Node, NodeCategory
from nodes.node_implementations.animator import AnimatorNode
from nodes.node_implementations.blaze_maker import BlazeMakerNode
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
from nodes.node_implementations.list_selector import ListSelectorNode
from nodes.node_implementations.overlay import OverlayNode
from nodes.node_implementations.port_forwarder import PortForwarderNode
from nodes.node_implementations.random_iterator import RandomIteratorNode
from nodes.node_implementations.random_list_selector import RandomListSelectorNode
from nodes.node_implementations.random_node_animator import RandomAnimatorNode
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
    AnimatorNode,
    RandomAnimatorNode,
    ListSelectorNode
]


def get_node_classes() -> list[tuple[NodeCategory, list[type[Node]]]]:
    category_map = defaultdict(list)
    for node_cls in node_classes:
        category = node_cls.node_category()
        category_map[category].append(node_cls)

    # Sort nodes in each category by name
    result: list[tuple[NodeCategory, list[type[Node]]]] = []
    for category, nodes in category_map.items():
        sorted_nodes = sorted(nodes, key=lambda n: n.name())
        result.append((category, sorted_nodes))

    # Sort by enum order
    result.sort(key=lambda x: x[0].value[0])
    return result
