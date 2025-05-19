from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps
from ui.nodes.nodes import UnitNode
from ui.nodes.prop_defs import PropDef, PortStatus, PT_Colour, Colour

DEF_COLOUR_NODE_INFO = PrivateNodeInfo(
    description="Outputs a desired colour.",
    prop_defs={
        'colour': PropDef(
            prop_type=PT_Colour(),
            display_name="Output colour",
            description="Colour",
            default_value=Colour(0, 0, 0, 255)
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Colour",
            display_in_props=False
        )
    }
)



class ColourNode(UnitNode):
    NAME = "Colour"
    DEFAULT_NODE_INFO = DEF_COLOUR_NODE_INFO

    def compute(self, props: ResolvedProps, *args):
        return {'_main': props.get('colour')}
