from ui.nodes.blaze_maker import BlazeMakerNode
from ui.nodes.canvas import CanvasNode
from ui.nodes.checkerboard import CheckerboardNode
from ui.nodes.colour import ColourNode
from ui.nodes.colour_filler import ColourFillerNode
from ui.nodes.colour_list import ColourListNode
from ui.nodes.ellipse_sampler import EllipseSamplerNode
from ui.nodes.function import FunctionNode
from ui.nodes.function_sampler import FunSamplerNode
from ui.nodes.gradient import GradientNode
from ui.nodes.grid import GridNode
from ui.nodes.iterator import IteratorNode
from ui.nodes.iterator_selector import IteratorSelectorNode
from ui.nodes.overlay import OverlayNode
from ui.nodes.shape import ShapeNode, PolygonNode
from ui.nodes.shape_repeater import ShapeRepeaterNode
from ui.nodes.stacker import StackerNode
from ui.nodes.warp import WarpNode

node_classes = [GridNode, ShapeNode, ShapeRepeaterNode, CheckerboardNode, WarpNode,
                FunctionNode, CanvasNode, IteratorNode, ColourListNode, FunSamplerNode, ColourFillerNode, OverlayNode,
                GradientNode, IteratorSelectorNode, EllipseSamplerNode, BlazeMakerNode, StackerNode, ColourNode]
