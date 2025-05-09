from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode, CombinationNode
from ui.nodes.port_defs import PortDef, PortIO, PT_Warp, PT_Function
from ui.nodes.warp_utils import PosWarp, RelWarp
from ui.vis_types import MatplotlibFig

DEF_POS_WARP_NODE_INFO = NodeInfo(
    description="Given a function, convert it to a warp by normalising f(x) to be between 0 & 1 for x ∈ [0,1]. The input function must pass through the origin.",
    port_defs={
        (PortIO.INPUT, 'function'): PortDef("Function", PT_Function()),
        (PortIO.OUTPUT, '_main'): PortDef("Warp", PT_Warp())
    }
)


class PosWarpNode(UnitNode):
    NAME = "Position Warp"
    DEFAULT_NODE_INFO = DEF_POS_WARP_NODE_INFO

    @staticmethod
    def helper(function):
        return PosWarp(function)

    def compute(self, out_port_key='_main'):
        f = self._prop_val('function')
        if f:
            try:
                warp = PosWarpNode.helper(f)
            except ValueError as e:
                raise NodeInputException(str(e), self.uid)
            return warp
        return None

    def visualise(self):
        warp = self.compute()
        if warp:
            return MatplotlibFig(create_graph_svg(warp.sample(1000)))
        return None


DEF_REL_WARP_NODE_INFO = NodeInfo(
    description="Given a function, use it to accumulate positions based on evenly spaced indices between 0 & 1, giving a new list of samples which are normalised between 0 & 1. The input function must pass through the origin.",
    port_defs={
        (PortIO.INPUT, 'function'): PortDef("Function", PT_Function()),
        (PortIO.OUTPUT, '_main'): PortDef("Warp", PT_Warp())
    }
)


class RelWarpNode(UnitNode):
    NAME = "Relative Warp"
    DEFAULT_NODE_INFO = DEF_REL_WARP_NODE_INFO

    @staticmethod
    def helper(function):
        return RelWarp(function)

    def compute(self, out_port_key='_main'):
        f = self._prop_val('function')
        if f:
            try:
                warp = RelWarpNode.helper(f)
            except ValueError as e:
                raise NodeInputException(str(e), self.uid)
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
