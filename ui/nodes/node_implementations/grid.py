from typing import Optional

from ui.id_datatypes import PropKey
from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps
from ui.nodes.node_implementations.visualiser import get_grid, add_background
from ui.nodes.nodes import UnitNode
from ui.nodes.prop_defs import PT_Warp, PT_Grid, PT_Int, PropDef, Colour, PortStatus, Int, PropValue, Grid
from ui.nodes.shape_datatypes import Group, Polyline
from ui.vis_types import Visualisable

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
               '_main': PropDef(input_port_status=PortStatus.FORBIDDEN,
                                output_port_status=PortStatus.COMPULSORY,
                                display_name="Grid")
               }
)


class GridNode(UnitNode):
    NAME = "Grid"
    DEFAULT_NODE_INFO = DEF_GRID_INFO

    def compute(self, props: ResolvedProps, _):
        return {'_main': get_grid(props.get('width'), props.get('height'), props.get('x_warp'), props.get('y_warp'))}

    def visualise(self, compute_results: dict[PropKey, PropValue]) -> Optional[Visualisable]:
        grid: Grid = compute_results.get('_main')
        grid_group = Group(debug_info="Grid")
        for x in grid.v_line_xs:
            # Draw horizontal lines
            grid_group.add(Polyline([(x, 0), (x, 1)], stroke='black', stroke_width=2))
        for y in grid.h_line_ys:
            # Draw vertical lines
            grid_group.add(Polyline([(0, y), (1, y)], stroke='black', stroke_width=2))
        return add_background(grid_group, Colour(255, 255, 255, 255))
