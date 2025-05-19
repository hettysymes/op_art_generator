# from ui.nodes.node_defs import PrivateNodeInfo
# from ui.nodes.prop_defs import PropDef, PT_List, PortStatus
#
# DEF_COLOUR_LIST_INFO = PrivateNodeInfo(
#     description="Define a list of colours. This can be provided as input to an Iterator or a Colour Filler.",
#     prop_defs={
#         'import_colours': PropDef(
#             prop_type=PT_List(PT_Colour()),
#             display_name="Import Colours"
#         ),
#         'colour_order': PropDef(
#             prop_type=PT_ColourRefTable('import_colours'),
#             display_name="Colours",
#             description="Colours to populate the colour list.",
#             default_value=[(0, 0, 0, 255), (255, 0, 0, 255), (0, 255, 0, 255)]
#         ),
#         '_main': PropDef(
#             input_port_status=PortStatus.FORBIDDEN,
#             output_port_status=PortStatus.COMPULSORY,
#             display_name="Colours"
#         )
#     }
# )
#
#
#
# class ColourListNode(SelectableNode):
#     NAME = "Colour List"
#     DEFAULT_NODE_INFO = DEF_COLOUR_LIST_INFO
#
#     def compute(self):
#         ref_colours = self._prop_val('import_colours', get_refs=True)
#         colours = handle_port_ref_table(ref_colours, self._prop_val('colour_order'))
#         self.set_compute_result(colours)
#         for port_id in self.extracted_port_ids:
#             _, port_key = port_id
#             _, i = port_key.split('_')
#             self.set_compute_result(colours[int(i)], port_key=port_key)
#
#     def visualise(self):
#         return visualise_by_type(self.get_compute_result(), PT_List(PT_Colour()))
#
#     def extract_element(self, parent_group, element_id):
#         i = parent_group.get_element_index_from_id(element_id)
#         # Add new port definition
#         port_id = (PortIO.OUTPUT, f'colour_{i}')
#         port_def = PortDef(f"Colour {i}", PT_Colour())
#         self._add_port(port_id, port_def)  # TODO put this functionality in parent class
#         return port_id
#
#     def _is_port_redundant(self, port_id):
#         colours = self._prop_val('colour_order')
#         _, port_key = port_id
#         _, i = port_key.split('_')
#         return int(i) >= len(colours)
