from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape import RectangleNode
from ui.nodes.shape_datatypes import Group
from ui.port_defs import PortDef, PT_Colour, PT_Fill

COLOUR_NODE_INFO = UnitNodeInfo(
    name="Colour",
    prop_port_defs=[PortDef('Colour', PT_Fill, key_name='colour')],
    out_port_defs=[PortDef("Colour", PT_Colour)],
    prop_type_list=PropTypeList([
        PropType("colour", "colour", default_value=(0, 0, 0, 255),
                 description="Output colour.", display_name="Colour", port_modifiable=True)
    ]),
    description="Outputs a desired colour."
)


class ColourNode(UnitNode):
    UNIT_NODE_INFO = COLOUR_NODE_INFO

    def compute(self):
        return self.get_prop_val('colour')

    def visualise(self):
        group = Group(debug_info="Colour")
        group.add(RectangleNode.helper(self.compute()))
        return group
