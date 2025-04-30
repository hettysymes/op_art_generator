from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.elem_ref import ElemRef
from ui.nodes.multi_input_handler import handle_multi_inputs
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape import RectangleNode
from ui.nodes.shape_datatypes import Group
from ui.nodes.utils import process_rgb
from ui.port_defs import PortType, PortDef, PT_Element, PT_Colour

COLOUR_NODE_INFO = UnitNodeInfo(
    name="Colour",
    resizable=True,
    selectable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Colour", PT_Colour)],
    prop_type_list=PropTypeList([
        PropType("colour", "colour", default_value=(0, 0, 0, 255),
                     description="Output colour.", display_name="Colour")
    ]),
    description="Outputs a desired colour."
)


class ColourNode(UnitNode):
    UNIT_NODE_INFO = COLOUR_NODE_INFO

    def compute(self):
        return self.get_prop_val('colour')

    def visualise(self, temp_dir, height, wh_ratio):
        colour = self.compute()
        fill, fill_opacity = process_rgb(colour)
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (RectangleNode.helper(fill, fill_opacity), None)).save()
