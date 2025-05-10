from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_implementations.shape import RectangleNode
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Colour
from ui.nodes.prop_defs import PropEntry, PrT_Fill
from ui.nodes.shape_datatypes import Group

DEF_COLOUR_NODE_INFO = NodeInfo(
    description="Outputs a desired colour.",
    port_defs={(PortIO.INPUT, 'colour'): PortDef("Colour", PT_Colour(), optional=True),
               (PortIO.OUTPUT, '_main'): PortDef("Colour", PT_Colour())},
    prop_entries={'colour': PropEntry(PrT_Fill(),
                                      display_name="Output colour.",
                                      description="Colour",
                                      default_value=(0, 0, 0, 255))}
)


class ColourNode(UnitNode):
    NAME = "Colour"
    DEFAULT_NODE_INFO = DEF_COLOUR_NODE_INFO

    def compute(self, out_port_key='_main'):
        return self._prop_val('colour')

    def visualise(self):
        group = Group(debug_info="Colour")
        group.add(RectangleNode.helper(self.compute()))
        return group
