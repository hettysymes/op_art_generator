import itertools

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList
from ui.nodes.shape_datatypes import Group, Polyline, Polygon, Element
from ui.nodes.utils import process_rgb
from ui.port_defs import PortDef, PT_ColourList, PT_Element

COLOUR_FILLER_NODE_INFO = UnitNodeInfo(
    name="Colour Filler",
    resizable=True,
    selectable=True,
    in_port_defs=[
        PortDef("Colours", PT_ColourList, key_name='colour_list'),
        PortDef("Drawing", PT_Element, key_name='element')
    ],
    out_port_defs=[PortDef("Drawing", PT_Element)],
    prop_type_list=PropTypeList([]),
    description="Given a colour list and a drawing consisting of lines, cycle through the colours and use them to fill the gaps between the lines."
)


class ColourFillerNode(UnitNode):
    UNIT_NODE_INFO = COLOUR_FILLER_NODE_INFO

    @staticmethod
    def helper(colours, element):
        ret_group = Group()
        colour_it = itertools.cycle(colours)
        transformed_shapes = element.transformed_shapes()
        for i in range(1, len(transformed_shapes)):
            shape1, transform_list1 = transformed_shapes[i - 1]
            shape2, transform_list2 = transformed_shapes[i]
            points = shape1.get_points(transform_list1) + list(reversed(shape2.get_points(transform_list2)))
            fill, fill_opacity = process_rgb(next(colour_it))
            ret_group.add(Polygon(points, fill, fill_opacity))
        return ret_group

    def compute(self):
        colours = self.get_input_node('colour_list').compute()
        element: Element = self.get_input_node('element').compute()
        if (colours is not None) and element:
            if not colours:
                raise NodeInputException("Input colour list must contain at least one colour.", self.node_id)
            # Check all shapes are polylines
            for transformed_shape in element.transformed_shapes():
                if not isinstance(transformed_shape[0], Polyline):
                    raise NodeInputException("Input drawing must only consist of lines.", self.node_id)
            return ColourFillerNode.helper(colours, element)
        return None

    def visualise(self, temp_dir, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (element, None)).save()
        return None
