from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.node_info import POS_WARP_NODE_INFO, REL_WARP_NODE_INFO
from ui.nodes.nodes import UnitNode, CombinationNode
from ui.nodes.warp_utils import PosWarp, RelWarp


class PosWarpNode(UnitNode):
    UNIT_NODE_INFO = POS_WARP_NODE_INFO

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def compute(self):
        f = self.input_nodes[0].compute()
        if f: return PosWarp(f)

    def visualise(self, height, wh_ratio):
        warp = self.compute()
        if warp:
            return create_graph_svg(height, wh_ratio, warp.sample(1000), f"tmp/{str(self.node_id)}")


class RelWarpNode(UnitNode):
    UNIT_NODE_INFO = REL_WARP_NODE_INFO

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def compute(self):
        f = self.input_nodes[0].compute()
        if f: return RelWarp(f)

    def visualise(self, height, wh_ratio):
        warp = self.compute()
        if warp:
            return create_graph_svg(height, wh_ratio, warp.sample(1000), f"tmp/{str(self.node_id)}")


class WarpNode(CombinationNode):
    NAME = "Warp"
    SELECTIONS = [PosWarpNode, RelWarpNode]
