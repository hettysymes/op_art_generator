# from ui.nodes.node_defs import NodeInfo
# from ui.nodes.nodes import UnitNode
# from ui.nodes.prop_defs import PortIO, PortDef, PT_Colour, PropEntry, PT_Fill
#
# DEF_COLOUR_NODE_INFO = NodeInfo(
#     description="Outputs a desired colour.",
#     port_defs={(PortIO.INPUT, 'colour'): PortDef("Colour", PT_Colour(), optional=True),
#                (PortIO.OUTPUT, '_main'): PortDef("Colour", PT_Colour())},
#     prop_entries={'colour': PropEntry(PT_Fill(),
#                                       display_name="Output colour",
#                                       description="Colour",
#                                       default_value=(0, 0, 0, 255))}
# )
#
#
# class ColourNode(UnitNode):
#     NAME = "Colour"
#     DEFAULT_NODE_INFO = DEF_COLOUR_NODE_INFO
#
#     def compute(self):
#         self.set_compute_result(self._prop_val('colour'))
from ui.nodes.prop_defs import PropValue, PropType, PT_Colour


