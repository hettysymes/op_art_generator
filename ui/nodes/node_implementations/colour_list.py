from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps
from ui.nodes.nodes import UnitNode
from ui.nodes.prop_defs import PropDef, PT_List, PortStatus, PT_Colour, Colour, List, PT_FillHolder, PT_Fill

DEF_COLOUR_LIST_INFO = PrivateNodeInfo(
    description="Define a list of colours. This can be provided as input to an Iterator or a Colour Filler.",
    prop_defs={
        'colours': PropDef(
            prop_type=PT_List(PT_FillHolder(), input_multiple=True),
            display_name="Colours",
            description="Colours to populate the colour list.",
            output_port_status=PortStatus.FORBIDDEN,
            default_value=List(PT_FillHolder(),
                               [Colour(0, 0, 0, 255), Colour(255, 0, 0, 255), Colour(0, 255, 0, 255)])
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Colours",
            display_in_props=False
        )
    }
)


class ColourListNode(UnitNode):
    NAME = "Colour List"
    DEFAULT_NODE_INFO = DEF_COLOUR_LIST_INFO

    def compute(self, props: ResolvedProps, *args):
        colours: List[PT_Fill] = List(PT_Fill(), [c_holder.fill for c_holder in props.get('colours')])
        return {'_main': colours}
