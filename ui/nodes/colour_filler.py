import itertools

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList
from ui.nodes.shape_datatypes import Element, Polyline, Polygon
from ui.nodes.utils import process_rgb
from ui.port_defs import PortDef, PortType, PT_ColourList, PT_Element

COLOUR_FILLER_NODE_INFO = UnitNodeInfo(
    name="Colour Filler",
    resizable=True,
    selectable=True,
    in_port_defs=[
        PortDef("Colours", PT_ColourList),
        PortDef("Drawing", PT_Element)
    ],
    out_port_defs=[PortDef("Drawing", PT_Element)],
    prop_type_list=PropTypeList([]),
    description="Given a colour list and a drawing consisting of lines, cycle through the colours and use them to fill the gaps between the lines."
)


class ColourFillerNode(UnitNode):
    UNIT_NODE_INFO = COLOUR_FILLER_NODE_INFO

    def compute(self):
        colours = self.input_nodes[0].compute()
        element = self.input_nodes[1].compute()
        if (colours is not None) and element:
            if not colours:
                raise NodeInputException("Input colour list must contain at least one colour.", self.node_id)
            ret_elem = Element()
            colour_it = itertools.cycle(colours)
            # Check all elements are polylines
            for shape in element:
                if not isinstance(shape, Polyline):
                    raise NodeInputException("Input drawing must only consist of lines.", self.node_id)
            for i in range(1, len(element)):
                points = element[i - 1].get_points() + list(reversed(element[i].get_points()))
                fill, fill_opacity = process_rgb(next(colour_it))
                ret_elem.add(Polygon(points, fill, fill_opacity))
            return ret_elem

    def visualise(self, temp_dir, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (element, None)).save()
