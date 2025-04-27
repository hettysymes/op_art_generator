from ui.nodes.drawers.grid_drawer import GridDrawing
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.warp_utils import PosWarp, RelWarp
from ui.port_defs import PortDef, PortType, PT_Warp, PT_Grid

GRID_NODE_INFO = UnitNodeInfo(
    name="Grid",
    resizable=True,
    selectable=False,
    in_port_defs=[PortDef("X Warp", PT_Warp), PortDef("Y Warp", PT_Warp)],
    out_port_defs=[PortDef("Grid", PT_Grid)],
    prop_type_list=PropTypeList(
        [
            PropType("width", "int", default_value=5,
                     description="Number of squares in width of grid"),
            PropType("height", "int", default_value=5,
                     description="Number of squares in height of grid")
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
        x_warp = self.input_nodes[0].compute()
        y_warp = self.input_nodes[1].compute()
        return GridNode.helper(x_warp, y_warp, self.prop_vals['width'], self.prop_vals['height'])

    def visualise(self, temp_dir, height, wh_ratio):
        return GridDrawing(self._return_path(temp_dir), height, wh_ratio, self.compute()).save()
