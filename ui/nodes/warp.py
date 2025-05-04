from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode, CombinationNode, UnitNodeInfo
from ui.nodes.warp_utils import PosWarp, RelWarp
from ui.port_defs import PortDef, PT_Function, PT_Warp
from ui.vis_types import MatplotlibFig

POS_WARP_NODE_INFO = UnitNodeInfo(
    name="Position Warp",
    selectable=False,
    in_port_defs=[PortDef("Function", PT_Function, key_name='function')],
    out_port_defs=[PortDef("Warp", PT_Warp)],
    description="Given a function, convert it to a warp by normalising f(x) to be between 0 & 1 for x ∈ [0,1]. The input function must pass through the origin."
)


class PosWarpNode(UnitNode):
    UNIT_NODE_INFO = POS_WARP_NODE_INFO

    @staticmethod
    def helper(function):
        return PosWarp(function)

    def compute(self):
        f = self.get_input_node('function').compute()
        if f:
            try:
                warp = PosWarpNode.helper(f)
            except ValueError as e:
                raise NodeInputException(str(e), self.node_id)
            return warp
        return None

    def visualise(self):
        warp = self.compute()
        if warp:
            return MatplotlibFig(create_graph_svg(warp.sample(1000)))
        return None


REL_WARP_NODE_INFO = UnitNodeInfo(
    name="Relative Warp",
    selectable=False,
    in_port_defs=[PortDef("Function", PT_Function, key_name='function')],
    out_port_defs=[PortDef("Warp", PT_Warp)],
    description="Given a function, use it to accumulate positions based on evenly spaced indices between 0 & 1, giving a new list of samples which are normalised between 0 & 1. The input function must pass through the origin."
)


class RelWarpNode(UnitNode):
    UNIT_NODE_INFO = REL_WARP_NODE_INFO

    @staticmethod
    def helper(function):
        return RelWarp(function)

    def compute(self):
        f = self.get_input_node('function').compute()
        if f:
            try:
                warp = RelWarpNode.helper(f)
            except ValueError as e:
                raise NodeInputException(str(e), self.node_id)
            return warp
        return None

    def visualise(self):
        warp = self.compute()
        if warp:
            return MatplotlibFig(create_graph_svg(warp.sample(1000)))
        return None


class WarpNode(CombinationNode):
    NAME = "Warp"
    SELECTIONS = [PosWarpNode, RelWarpNode]
