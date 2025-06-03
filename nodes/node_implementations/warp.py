from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory
from nodes.node_input_exception import NodeInputException
from nodes.nodes import UnitNode, CombinationNode
from nodes.prop_types import PT_Function, PT_Warp
from nodes.warp_datatypes import PosWarp, RelWarp

DEF_POS_WARP_NODE_INFO = PrivateNodeInfo(
    description="Given a function, convert it to a warp by normalising f(x) to be between 0 & 1 for x ∈ [0,1]. The input function must pass through the origin.",
    prop_defs={
        'function': PropDef(
            prop_type=PT_Function(),
            display_name="Function",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            display_in_props=False
        ),
        '_main': PropDef(
            prop_type=PT_Warp(),
            display_name="Warp",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_in_props=False
        )
    }
)


class PosWarpNode(UnitNode):
    NAME = "Position Warp"
    NODE_CATEGORY = NodeCategory.PROPERTY_MODIFIER
    DEFAULT_NODE_INFO = DEF_POS_WARP_NODE_INFO

    @staticmethod
    def helper(function):
        return PosWarp(function)

    def compute(self, props: ResolvedProps, *args):
        f = props.get('function')
        if f:
            try:
                warp = PosWarpNode.helper(f)
            except ValueError as e:
                raise NodeInputException(e)
            return {'_main': warp}
        return {}


DEF_REL_WARP_NODE_INFO = PrivateNodeInfo(
    description="Given a function, use it to accumulate positions based on evenly spaced indices between 0 & 1, giving a new list of samples which are normalised between 0 & 1. The input function must pass through the origin.",
    prop_defs={
        'function': PropDef(
            prop_type=PT_Function(),
            display_name="Function",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            display_in_props=False
        ),
        '_main': PropDef(
            prop_type=PT_Warp(),
            display_name="Warp",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_in_props=False
        )
    }
)


class RelWarpNode(UnitNode):
    NAME = "Relative Warp"
    NODE_CATEGORY = NodeCategory.PROPERTY_MODIFIER
    DEFAULT_NODE_INFO = DEF_REL_WARP_NODE_INFO

    @staticmethod
    def helper(function):
        return RelWarp(function)

    def compute(self, props: ResolvedProps, *args):
        f = props.get('function')
        if f:
            try:
                warp = RelWarpNode.helper(f)
            except ValueError as e:
                raise NodeInputException(str(e))
            return {'_main': warp}
        return {}


class WarpNode(CombinationNode):
    NAME = "Warp"
    NODE_CATEGORY = NodeCategory.PROPERTY_MODIFIER
    SELECTIONS = [PosWarpNode, RelWarpNode]
