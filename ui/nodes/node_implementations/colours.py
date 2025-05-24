from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps
from ui.nodes.nodes import UnitNode, CombinationNode
from ui.nodes.prop_defs import PropDef, PortStatus, Colour, PT_Colour, PT_List, PT_GradOffset, List, PT_Point, Point, \
    GradOffset, Gradient

DEF_COLOUR_NODE_INFO = PrivateNodeInfo(
    description="Outputs a desired solid colour.",
    prop_defs={
        'colour': PropDef(
            prop_type=PT_Colour(),
            display_name="Colour",
            description="Solid colour.",
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

DEF_GRADIENT_NODE_INFO = PrivateNodeInfo(
    description="Define a linear gradient. This can be passed to a shape node as its fill.",
    prop_defs={
        'start_coord': PropDef(
            prop_type=PT_Point(),
            display_name="Gradient start coordinate",
            description="Coordinate of the gradient start. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Point(0, 0)
        ),
        'stop_coord': PropDef(
            prop_type=PT_Point(),
            display_name="Gradient stop coordinate",
            description="Coordinate of the gradient stop. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Point(1, 0)
        ),
        'grad_offsets': PropDef(
            prop_type=PT_List(PT_GradOffset()),
            display_name="Colour offsets",
            description="Colours at different offsets",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN,
            default_value=List(PT_GradOffset(), [GradOffset(0, Colour(255, 255, 255, 0)), GradOffset(1, Colour(255, 255, 255, 255))])
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
    NAME = "Linear Gradient"
    DEFAULT_NODE_INFO = DEF_GRADIENT_NODE_INFO

    def compute(self, props: ResolvedProps, *args):
        return {'_main': Gradient(props.get('start_coord'), props.get('stop_coord'), props.get('grad_offsets'))}

class FillNode(CombinationNode):
    NAME = "Fill"
    SELECTIONS = [ColourNode, GradientNode]
