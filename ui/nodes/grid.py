from ui.nodes.drawers.grid_drawer import GridDrawing
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape import StraightLineNode
from ui.nodes.shape_datatypes import Group
from ui.nodes.warp_utils import PosWarp, RelWarp
from ui.port_defs import PortDef, PT_Warp, PT_Grid

GRID_NODE_INFO = UnitNodeInfo(
    name="Grid",
    resizable=True,
    selectable=False,
    in_port_defs=[PortDef("X Warp", PT_Warp, key_name='x_warp'), PortDef("Y Warp", PT_Warp, key_name='y_warp')],
    out_port_defs=[PortDef("Grid", PT_Grid)],
    prop_type_list=PropTypeList(
        [
            PropType("width", "int", default_value=5, min_value=1,
                     description="Number of cells in the width of the grid, at most 1.", display_name="Width"),
            PropType("height", "int", default_value=5, min_value=1,
                     description="Number of cells in the height of the grid, at most 1.", display_name="Height")
        ]
    ),
    description="Define a grid, which can be input to a Shape Repeater or Checkerboard node. The spacing between the vertical and horizontal lines of the grid can be altered via a Warp in the X or Y direction respectively."
)


class GridNode(UnitNode):
    UNIT_NODE_INFO = GRID_NODE_INFO

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
        x_warp = self.get_input_node('x_warp').compute()
        y_warp = self.get_input_node('y_warp').compute()
        return GridNode.helper(x_warp, y_warp, self.get_prop_val('width'), self.get_prop_val('height'))

    def visualise(self):
        v_line_xs, h_line_ys = self.compute()
        print("Xs and Ys")
        print(v_line_xs, h_line_ys)
        group = Group(debug_info="Grid")
        for x in v_line_xs:
            # Draw horizontal lines
            group.add(StraightLineNode.helper((x, 0), (x, 1), stroke='black', stroke_width=1))
        for y in h_line_ys:
            # Draw vertical lines
            group.add(StraightLineNode.helper((0, y), (1, y), stroke='black', stroke_width=1))
        return group
