from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory, DisplayStatus
from nodes.nodes import UnitNode, CombinationNode
from nodes.prop_types import PT_Colour, PT_List, PT_GradOffset, PT_Point, PT_Gradient, PT_Number, PT_Int
from nodes.prop_values import List, Point, Colour, Gradient, GradOffset, Float

DEF_COLOUR_NODE_INFO = PrivateNodeInfo(
    description="Outputs a desired solid colour.",
    prop_defs={
        'colour': PropDef(
            prop_type=PT_Colour(),
            display_name="Colour",
            description="Solid colour.",
            default_value=Colour(0, 0, 0, 255)
        ),
        'red': PropDef(
            prop_type=PT_Int(min_value=0, max_value=255),
            display_name="Red",
            description="Red component of the colour.",
            display_status=DisplayStatus.PORT_ONLY_DISPLAY
        ),
        'green': PropDef(
            prop_type=PT_Int(min_value=0, max_value=255),
            display_name="Green",
            description="Green component of the colour.",
            display_status=DisplayStatus.PORT_ONLY_DISPLAY
        ),
        'blue': PropDef(
            prop_type=PT_Int(min_value=0, max_value=255),
            display_name="Blue",
            description="Blue component of the colour.",
            display_status=DisplayStatus.PORT_ONLY_DISPLAY
        ),
        'alpha': PropDef(
            prop_type=PT_Number(min_value=0, max_value=255),
            display_name="Alpha",
            description="Alpha component of the colour.",
            display_status=DisplayStatus.PORT_ONLY_DISPLAY
        ),
        '_main': PropDef(
            prop_type=PT_Colour(),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Colour",
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class ColourNode(UnitNode):
    NAME = "Solid Colour"
    NODE_CATEGORY = NodeCategory.BASE_PROPERTY
    DEFAULT_NODE_INFO = DEF_COLOUR_NODE_INFO

    def compute(self, props: ResolvedProps, *args):
        r, g, b, a = props.get('colour')

        # Override RGBA input port values
        r_prop = props.get('red')
        g_prop = props.get('green')
        b_prop = props.get('blue')
        a_prop = props.get('alpha')

        r = r if r_prop is None else r_prop
        g = g if g_prop is None else g_prop
        b = b if b_prop is None else b_prop
        a = a if a_prop is None else a_prop

        return {'_main': Colour(r,g,b,a)}


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
            display_name="Gradient end coordinate",
            description="Coordinate of the gradient end. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Point(1, 0)
        ),
        'grad_offsets': PropDef(
            prop_type=PT_List(PT_GradOffset()),
            display_name="Colour stops",
            description="Specify solid colours and their respective offsets in the gradient.",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN,
            default_value=List(PT_GradOffset(),
                               [GradOffset(0, Colour(255, 255, 255, 0)), GradOffset(1, Colour(255, 255, 255, 255))])
        ),
        '_main': PropDef(
            prop_type=PT_Gradient(),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Gradient",
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class GradientNode(UnitNode):
    NAME = "Linear Gradient"
    NODE_CATEGORY = NodeCategory.BASE_PROPERTY
    DEFAULT_NODE_INFO = DEF_GRADIENT_NODE_INFO

    def compute(self, props: ResolvedProps, *args):
        return {'_main': Gradient(props.get('start_coord'), props.get('stop_coord'), props.get('grad_offsets'))}


class FillNode(CombinationNode):
    NAME = "Colour"
    NODE_CATEGORY = NodeCategory.BASE_PROPERTY
    SELECTIONS = [ColourNode, GradientNode]
