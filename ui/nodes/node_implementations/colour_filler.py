import itertools

from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortDef, PortIO, PT_Element, PT_List, PT_Colour
from ui.nodes.shape_datatypes import Group, Polygon, Element, Polyline
from ui.nodes.utils import process_rgb

DEF_COLOUR_FILLER_INFO = NodeInfo(
    description="Given a colour list and a drawing consisting of lines, cycle through the colours and use them to fill the gaps between the lines.",
    port_defs={
        (PortIO.INPUT, 'colour_list'): PortDef("Colours", PT_List(PT_Colour())),
        (PortIO.INPUT, 'element'): PortDef("Drawing", PT_Element()),
        (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Element())
    },
    prop_entries={}
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
            points = shape1.get_points(transform_list1) + list(reversed(shape2.get_points(transform_list2)))
            fill, fill_opacity = process_rgb(next(colour_it))
            ret_group.add(Polygon(points, fill, fill_opacity))
        return ret_group

    def compute(self, out_port_key='_main'):
        colours = self._prop_val('colour_list')
        element: Element = self._prop_val('element')
        if (colours is not None) and element:
            if not colours:
                raise NodeInputException("Input colour list must contain at least one colour.", self.uid)
            # Check all shapes are polylines
            for transformed_shape in element.shape_transformations():
                if not isinstance(transformed_shape[0], Polyline):
                    raise NodeInputException("Input drawing must only consist of lines.", self.uid)
            return ColourFillerNode.helper(colours, element)
        return None
