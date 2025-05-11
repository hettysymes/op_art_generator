from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_implementations.canvas import CanvasNode
from ui.nodes.node_implementations.shape import StraightLineNode
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Warp, PT_Grid, PT_Int, PropEntry
from ui.nodes.shape_datatypes import Group
from ui.nodes.warp_utils import PosWarp, RelWarp

DEF_GRID_INFO = NodeInfo(
    description="Define a grid, which can be input to a Shape Repeater or Checkerboard node. The spacing between the vertical and horizontal lines of the grid can be altered via a Warp in the X or Y direction respectively.",
    port_defs={(PortIO.INPUT, 'x_warp'): PortDef("X Warp", PT_Warp(), optional=True, description="By default vertical grid lines are spaced equally."),
               (PortIO.INPUT, 'y_warp'): PortDef("Y Warp", PT_Warp(), optional=True, description="By default horizontal grid lines are spaced equally."),
               (PortIO.OUTPUT, '_main'): PortDef("Grid", PT_Grid())},
    prop_entries={'width': PropEntry(PT_Int(min_value=1),
                                     display_name="Width",
                                     description="Number of cells in the width of the grid, at most 1.",
                                     default_value=5),
                  'height': PropEntry(PT_Int(min_value=1),
                                      display_name="Height",
                                      description="Number of cells in the height of the grid, at most 1.",
                                      default_value=5)}
)


class GridNode(UnitNode):
    NAME = "Grid"
    DEFAULT_NODE_INFO = DEF_GRID_INFO

    @staticmethod
    def helper(x_warp, y_warp, width, height):
        if x_warp is None:
            x_warp = PosWarp(lambda i: i)
        else:
            assert isinstance(x_warp, PosWarp) or isinstance(x_warp, RelWarp)

        if y_warp is None:
            y_warp = PosWarp(lambda i: i)
        else:
            assert isinstance(y_warp, PosWarp) or isinstance(y_warp, RelWarp)

        v_line_xs = x_warp.sample(width + 1)
        h_line_ys = y_warp.sample(height + 1)
        return v_line_xs, h_line_ys

    def compute(self):
        # Get warp functions
        x_warp = self._prop_val('x_warp')
        y_warp = self._prop_val('y_warp')
        self.set_compute_result(GridNode.helper(x_warp, y_warp, self._prop_val('width'), self._prop_val('height')))

    def visualise(self):
        v_line_xs, h_line_ys = self.get_compute_result()
        grid_group = Group(debug_info="Grid")
        for x in v_line_xs:
            # Draw horizontal lines
            grid_group.add(StraightLineNode.helper((x, 0), (x, 1), stroke='black', stroke_width=2))
        for y in h_line_ys:
            # Draw vertical lines
            grid_group.add(StraightLineNode.helper((0, y), (1, y), stroke='black', stroke_width=2))
        return CanvasNode.helper((255, 255, 255, 255), grid_group)
