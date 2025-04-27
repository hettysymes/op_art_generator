from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.nodes import UnitNode, CombinationNode, UnitNodeInfo, PropTypeList
from ui.nodes.warp_utils import PosWarp, RelWarp
from ui.port_defs import PortDef, PortType

POS_WARP_NODE_INFO = UnitNodeInfo(
    name="Position Warp",
    resizable=True,
    selectable=False,
    in_port_defs=[PortDef("Function", PortType.FUNCTION)],
    out_port_defs=[PortDef("Warp", PortType.WARP)],
    prop_type_list=PropTypeList([]),
    description="Given a function, convert it to a warp by normalising f(x) to be between 0 & 1 for x ∈ [0,1]. The input function must pass through the origin."
)


class PosWarpNode(UnitNode):
    UNIT_NODE_INFO = POS_WARP_NODE_INFO

    def compute(self):
        f = self.input_nodes[0].compute()
        if f: return PosWarp(f)

    def visualise(self, temp_dir, height, wh_ratio):
        warp = self.compute()
        if warp:
            return create_graph_svg(height, wh_ratio, warp.sample(1000), self._return_path(temp_dir))


REL_WARP_NODE_INFO = UnitNodeInfo(
    name="Relative Warp",
    resizable=True,
    selectable=False,
    in_port_defs=[PortDef("Function", PortType.FUNCTION)],
    out_port_defs=[PortDef("Warp", PortType.WARP)],
    prop_type_list=PropTypeList([]),
    description="Given a function, use it to accumulate positions based on evenly spaced indices between 0 & 1, giving a new list of samples which are normalised between 0 & 1. The input function must pass through the origin."
)


class RelWarpNode(UnitNode):
    UNIT_NODE_INFO = REL_WARP_NODE_INFO

    def compute(self):
        f = self.input_nodes[0].compute()
        if f: return RelWarp(f)

    def visualise(self, temp_dir, height, wh_ratio):
        warp = self.compute()
        if warp:
            return create_graph_svg(height, wh_ratio, warp.sample(1000), self._return_path(temp_dir))


class WarpNode(CombinationNode):
    NAME = "Warp"
    SELECTIONS = [PosWarpNode, RelWarpNode]
