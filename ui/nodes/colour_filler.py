import itertools

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList
from ui.nodes.shape_datatypes import Element, PolyLine, Polygon
from ui.nodes.utils import process_rgb
from ui.port_defs import PortDef, PortType

COLOUR_FILLER_NODE_INFO = UnitNodeInfo(
    name="Colour Filler",
    resizable=True,
    selectable=True,
    in_port_defs=[
        PortDef("Colours", PortType.VALUE_LIST),
        PortDef("Drawing", PortType.ELEMENT)
    ],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList([]),
    description="Given a colour list and a drawing consisting of lines, cycle through the colours and use them to fill the gaps between the lines."
)


class ColourFillerNode(UnitNode):
    UNIT_NODE_INFO = COLOUR_FILLER_NODE_INFO

    def compute(self):
        colours = self.input_nodes[0].compute()
        element = self.input_nodes[1].compute()
        if (colours is not None) and element:
            ret_elem = Element()
            colour_it = itertools.cycle(colours)
            for i in range(1, len(element)):
                assert isinstance(element[i - 1], PolyLine)
                assert isinstance(element[i], PolyLine)
                points = element[i - 1].get_points() + list(reversed(element[i].get_points()))
                fill, fill_opacity = process_rgb(next(colour_it))
                ret_elem.add(Polygon(points, fill, fill_opacity))
            return ret_elem

    def visualise(self, temp_dir, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (element, None)).save()
