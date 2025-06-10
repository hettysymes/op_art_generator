import itertools

from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory, DisplayStatus
from nodes.node_input_exception import NodeInputException
from nodes.nodes import UnitNode
from nodes.prop_types import PT_Element, PT_List, PT_FillHolder, PT_Point, \
    PT_Fill
from nodes.prop_values import List
from nodes.shape_datatypes import Group, Polygon, Element, Polyline

DEF_COLOUR_FILLER_INFO = PrivateNodeInfo(
    description="Given a colour list and a drawing consisting of lines, cycle through the colours and use them to fill the gaps between the lines.",
    prop_defs={
        'colours': PropDef(
            prop_type=PT_List(PT_FillHolder(), input_multiple=True),
            display_name="Colours",
            default_value=List(PT_FillHolder())
        ),
        'element': PropDef(
            prop_type=PT_Element(),
            display_name="Drawing",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            display_status=DisplayStatus.NO_DISPLAY
        ),
        '_main': PropDef(
            prop_type=PT_Element(),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Drawing",
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class ColourFillerNode(UnitNode):
    NAME = "Colour Filler"
    NODE_CATEGORY = NodeCategory.DRAWING_MODIFIER
    DEFAULT_NODE_INFO = DEF_COLOUR_FILLER_INFO

    @staticmethod
    def helper(colours, element):
        ret_group = Group(debug_info="Colour Filler")
        colour_it = itertools.cycle(colours)
        transformed_shapes = element.shape_transformations()
        for i in range(1, len(transformed_shapes)):
            shape1, transform_list1 = transformed_shapes[i - 1]
            shape2, transform_list2 = transformed_shapes[i]
            points: List[PT_Point] = transform_list1.transform_points(shape1.points) + transform_list2.transform_points(
                shape2.points).reversed()
            ret_group.add(Polygon(points.items, next(colour_it)))
        return ret_group

    def compute(self, props: ResolvedProps, *args):
        colours: List[PT_Fill] = List(PT_Fill(), [c_holder.fill for c_holder in props.get('colours')])
        element: Element = props.get('element')
        if not (colours and element):
            return {}
        # Check all shapes are polylines
        for transformed_shape in element.shape_transformations():
            if not isinstance(transformed_shape[0], Polyline):
                raise NodeInputException("Input drawing must only consist of lines.")
        return {'_main': ColourFillerNode.helper(colours, element)}
