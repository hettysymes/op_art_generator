# from ui.nodes.node_defs import NodeInfo
# from ui.nodes.node_implementations.port_ref_table_handler import handle_port_ref_table
# from ui.nodes.nodes import UnitNode
# from ui.nodes.prop_defs import PortIO, PortDef, PT_Element, PT_List, PT_ElemRefTable, PropEntry
# from ui.nodes.shape_datatypes import Group
#
# DEF_OVERLAY_INFO = NodeInfo(
#     description="Overlay 2+ drawings and define their order.",
#     port_defs={
#         (PortIO.INPUT, 'elements'): PortDef("Input Drawings", PT_List(PT_Element())),
#         (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Element())
#     },
#     prop_entries={
#         'elem_order': PropEntry(PT_ElemRefTable('elements'),
#                                 display_name="Drawing order",
#                                 description="Order of drawings in which to overlay them. Drawings at the top of the list are drawn first (i.e. at the bottom of the final overlayed image).",
#                                 default_value=[])
#     }
# )
#
#
# class OverlayNode(UnitNode):
#     NAME = "Overlay"
#     DEFAULT_NODE_INFO = DEF_OVERLAY_INFO
#
#     def compute(self):
#         ref_elements = self._prop_val('elements', get_refs=True)
#         elements = handle_port_ref_table(ref_elements, self._prop_val('elem_order'))
#         # Return final element
#         ret_group = Group(debug_info="Overlay")
#         for element in elements:
#             ret_group.add(element)
#         self.set_compute_result(ret_group)
