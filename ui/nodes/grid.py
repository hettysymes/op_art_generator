from ui.nodes.drawers.grid_drawer import GridDrawing
from ui.nodes.nodes import PropType, PropTypeList, UnitNode
from ui.nodes.warp_utils import PosWarp
from ui.port_defs import PortType, PortDef


class GridNode(UnitNode):
    DISPLAY = "Grid"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = GridNode.DISPLAY
        self.resizable = True
        self.in_port_defs = [PortDef("X Warp", PortType.WARP), PortDef("Y Warp", PortType.WARP)]
        self.out_port_defs = [PortDef("Grid", PortType.GRID)]
        self.prop_type_list = PropTypeList(
            [
                PropType("width", "int", default_value=5,
                         description="Number of squares in width of grid"),
                PropType("height", "int", default_value=5,
                         description="Number of squares in height of grid")
            ]
        )

    def compute(self):
        # Get warp functions
        x_warp = self.input_nodes[0].compute()
        if x_warp is None:
            x_warp = PosWarp(lambda i: i)
        else:
            assert isinstance(x_warp, PosWarp) or isinstance(x_warp, RelWarp)

        y_warp = self.input_nodes[1].compute()
        if y_warp is None:
            y_warp = PosWarp(lambda i: i)
        else:
            assert isinstance(y_warp, PosWarp) or isinstance(y_warp, RelWarp)

        v_line_xs = x_warp.sample(self.prop_vals['width'] + 1)
        h_line_ys = y_warp.sample(self.prop_vals['height'] + 1)
        return v_line_xs, h_line_ys

    def visualise(self, height, wh_ratio):
        return GridDrawing(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()
