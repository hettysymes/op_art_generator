from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus
from nodes.nodes import UnitNode
from nodes.prop_types import PropType

DEF_PORT_FORWARDER_INFO = PrivateNodeInfo(
    description="Forward a port to multiple ports. Useful when making custom nodes.",
    prop_defs={
        'input': PropDef(
            prop_type=PropType(),
            display_name="Input",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            display_in_props=False
        ),
        '_main': PropDef(
            display_name="Output",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_in_props=False
        )
    }
)


class PortForwarderNode(UnitNode):
    NAME = "Port Forwarder"
    DEFAULT_NODE_INFO = DEF_PORT_FORWARDER_INFO

    def compute(self, props: ResolvedProps, *args):
        input_val = props.get('input')
        if input_val is None:
            return {}
        return {'_main': input_val}
