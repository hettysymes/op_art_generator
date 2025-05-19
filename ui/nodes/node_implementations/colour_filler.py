import itertools

from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode
from ui.nodes.prop_defs import PropDef, PT_Element, PortStatus, PT_List, PT_Colour, List, PT_ColourHolder, PT_Point
from ui.nodes.shape_datatypes import Group, Polygon, Element, Polyline
from ui.nodes.utils import process_rgb

DEF_COLOUR_FILLER_INFO = PrivateNodeInfo(
    description="Given a colour list and a drawing consisting of lines, cycle through the colours and use them to fill the gaps between the lines.",
    prop_defs={
        'colours': PropDef(
            prop_type=PT_List(PT_ColourHolder(), input_multiple=True),
            display_name="Colours",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            default_value=List(PT_ColourHolder())
        ),
        'element': PropDef(
            prop_type=PT_Element(),
            display_name="Drawing",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            display_in_props=False
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Drawing",
            display_in_props=False
        )
    }
)



class ColourFillerNode(UnitNode):
    NAME = "Colour Filler"
    DEFAULT_NODE_INFO = DEF_COLOUR_FILLER_INFO

    @staticmethod
    def helper(colours, element):
        ret_group = Group(debug_info="Colour Filler")
        colour_it = itertools.cycle(colours)
        transformed_shapes = element.shape_transformations()
        for i in range(1, len(transformed_shapes)):
            shape1, transform_list1 = transformed_shapes[i - 1]
            shape2, transform_list2 = transformed_shapes[i]
            points: List[PT_Point] = transform_list1.transform_points(shape1.points) + transform_list2.transform_points(shape2.points).reversed()
            fill, fill_opacity = process_rgb(next(colour_it))
            ret_group.add(Polygon(points.items, fill, fill_opacity))
        return ret_group

    def compute(self, props: ResolvedProps, *args):
        colours: List[PT_Colour] = List(PT_Colour(), [c_holder.colour for c_holder in props.get('colours')])
        element: Element = props.get('element')
        if not (colours and element):
            return {}
        # Check all shapes are polylines
        for transformed_shape in element.shape_transformations():
            if not isinstance(transformed_shape[0], Polyline):
                raise NodeInputException("Input drawing must only consist of lines.")
        return {'_main': ColourFillerNode.helper(colours, element)}
