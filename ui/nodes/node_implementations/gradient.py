from ui.nodes.gradient_datatype import Gradient
from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps
from ui.nodes.nodes import UnitNode
from ui.nodes.prop_defs import PropDef, PortStatus, Colour, PT_Colour

DEF_GRADIENT_NODE_INFO = PrivateNodeInfo(
    description="Define a linear gradient. This can be passed to a shape node as its fill.",
    prop_defs={
        'start_col': PropDef(
            prop_type=PT_Colour(),
            display_name="Start colour",
            description="Starting colour of the gradient.",
            default_value=Colour(255, 255, 255, 0)
        ),
        'stop_col': PropDef(
            prop_type=PT_Colour(),
            display_name="Stop colour",
            description="Stop colour of the gradient.",
            default_value=Colour(255, 255, 255, 255)
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Gradient",
            display_in_props=False
        )
    }
)


class GradientNode(UnitNode):
    NAME = "Gradient"
    DEFAULT_NODE_INFO = DEF_GRADIENT_NODE_INFO

    def compute(self, props: ResolvedProps, *args):
        return {'_main': Gradient(props.get('start_col'), props.get('stop_col'))}
