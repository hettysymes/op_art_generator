from typing import Optional

from id_datatypes import PropKey
from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus
from nodes.node_implementations.visualiser import get_grid, add_background
from nodes.nodes import UnitNode
from nodes.prop_types import PT_Warp, PT_Int, PT_Grid
from nodes.prop_values import PropValue, Int, Grid, Colour
from nodes.shape_datatypes import Group, Polyline
from vis_types import Visualisable

DEF_GRID_INFO = PrivateNodeInfo(
    description="Define a grid, which can be input to a Shape Repeater or Checkerboard node. The spacing between the vertical and horizontal lines of the grid can be altered via a Warp in the X or Y direction respectively.",
    prop_defs={'width': PropDef(prop_type=PT_Int(min_value=1),
                                display_name="Width",
                                description="Number of cells in the width of the grid, at most 1.",
                                default_value=Int(5)),
               'height': PropDef(prop_type=PT_Int(min_value=1),
                                 display_name="Height",
                                 description="Number of cells in the height of the grid, at most 1.",
                                 default_value=Int(5)),
               'x_warp': PropDef(prop_type=PT_Warp(),
                                 display_name="X Warp",
                                 description="By default vertical grid lines are spaced equally."),
               'y_warp': PropDef(prop_type=PT_Warp(),
                                 display_name="Y Warp",
                                 description="By default horizontal grid lines are spaced equally."),
               '_main': PropDef(prop_type=PT_Grid(),
                                input_port_status=PortStatus.FORBIDDEN,
                                output_port_status=PortStatus.COMPULSORY,
                                display_name="Grid",
                                display_in_props=False)
               }
)


class GridNode(UnitNode):
    NAME = "Grid"
    DEFAULT_NODE_INFO = DEF_GRID_INFO

    def compute(self, props: ResolvedProps, *args):
        return {'_main': get_grid(props.get('width'), props.get('height'), props.get('x_warp'), props.get('y_warp'))}
