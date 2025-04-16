from ui.nodes.drawers.grid_drawer import GridDrawing
from ui.nodes.node_info import GRID_NODE_INFO
from ui.nodes.nodes import UnitNode
from ui.nodes.warp_utils import PosWarp, RelWarp


class GridNode(UnitNode):
    UNIT_NODE_INFO = GRID_NODE_INFO

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
