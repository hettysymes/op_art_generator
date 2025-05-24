from ui.nodes.gradient_datatype import Gradient
from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps
from ui.nodes.nodes import UnitNode
from ui.nodes.prop_defs import PropDef, PortStatus, Colour, PT_Colour, PT_List, PT_GradOffset, List

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
        'grad_offset': PropDef(
            prop_type=PT_List(PT_GradOffset()),
            display_name="Colour offsets",
            description="Colours at different offsets",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN,
            default_value=List(PT_GradOffset())
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
