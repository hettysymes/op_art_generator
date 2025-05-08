from ui_old.nodes.blaze_maker import BlazeMakerNode
from ui_old.nodes.canvas import CanvasNode
from ui_old.nodes.checkerboard import CheckerboardNode
from ui_old.nodes.colour import ColourNode
from ui_old.nodes.colour_filler import ColourFillerNode
from ui_old.nodes.colour_list import ColourListNode
from ui_old.nodes.drawing_group import DrawingGroupNode
from ui_old.nodes.ellipse_sampler import EllipseSamplerNode
from ui_old.nodes.function import FunctionNode
from ui_old.nodes.function_sampler import FunSamplerNode
from ui_old.nodes.gradient import GradientNode
from ui_old.nodes.grid import GridNode
from ui_old.nodes.iterator import IteratorNode
from ui_old.nodes.iterator_selector import IteratorSelectorNode
from ui_old.nodes.overlay import OverlayNode
from ui_old.nodes.random_colour_selector import RandomColourSelectorNode
from ui_old.nodes.shape import ShapeNode
from ui_old.nodes.shape_repeater import ShapeRepeaterNode
from ui_old.nodes.stacker import StackerNode
from ui_old.nodes.warp import WarpNode

node_classes = [GridNode, ShapeNode, ShapeRepeaterNode, CheckerboardNode, WarpNode,
                FunctionNode, CanvasNode, IteratorNode, ColourListNode, FunSamplerNode, ColourFillerNode, OverlayNode,
                GradientNode, IteratorSelectorNode, EllipseSamplerNode, BlazeMakerNode, StackerNode, ColourNode,
                RandomColourSelectorNode, DrawingGroupNode]
