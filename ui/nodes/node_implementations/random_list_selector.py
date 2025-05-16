# import random
#
# from ui.nodes.node_defs import NodeInfo
# from ui.nodes.node_input_exception import NodeInputException
# from ui.nodes.nodes import UnitNode
# from ui.nodes.prop_defs import PortIO, PortDef, PT_List, PT_Bool, PT_Int, PT_Hidden, PropEntry, PropType, \
#     get_most_general_type
#
# DEF_RANDOM_LIST_SELECTOR_INFO = NodeInfo(
#     description="Randomly select from a list.",
#     port_defs={
#         (PortIO.INPUT, 'list'): PortDef("List", PT_List()),
#         (PortIO.OUTPUT, '_main'): PortDef("Random selection", PropType())
#     },
#     prop_entries={
#         'use_seed': PropEntry(PT_Bool(),
#                               display_name="Use random seed?",
#                               description="If checked, use the provided seed for random selection. Random selections done with the same seed will always be the same.",
#                               default_value=False),
#         'user_seed': PropEntry(PT_Int(),
#                                display_name="Random seed",
#                                description="If random seed is used, use this as the random seed.",
#                                default_value=42),
#         '_actual_seed': PropEntry(PT_Hidden())
#     }
# )
#
#
# class RandomListSelectorNode(UnitNode):
#     NAME = "Random List Selector"
#     DEFAULT_NODE_INFO = DEF_RANDOM_LIST_SELECTOR_INFO
#
#     def compute(self):
#         val_list = self._prop_val('list', get_refs=True)
#         if not val_list:
#             # Update output port type
#             self.get_port_defs()[(PortIO.OUTPUT, '_main')].port_type = PropType()
#             return
#         # If one input, take input as the list. Else, choose one of the inputs
#         if len(val_list) == 1:
#             ref_id, values = next(iter(val_list.items()))
#             set_type = self._port_ref('list', ref_id).port_def.port_type.item_type
#         else:
#             port_defs = []
#             for ref_id, values in val_list.items():
#                 if not values:
#                     raise NodeInputException("List(s) must contain at least one item.", self.uid)
#                 port_defs.append(self._port_ref('list', ref_id).port_def.port_type)
#             set_type = get_most_general_type(port_defs)
#             values = list(val_list.values())
#         # Update output port type
#         self.get_port_defs()[(PortIO.OUTPUT, '_main')].port_type = set_type
#
#         # Update randomiser
#         if self._prop_val('use_seed'):
#             rng = random.Random(self._prop_val('user_seed'))
#         else:
#             rng = random.Random(self.get_seed())
#
#         # Set compute result
#         self.set_compute_result(rng.choice(values))
#
#     # Functions needed for randomisable node # TODO make into interface
#
#     def randomise(self, seed=None):
#         self.set_property('_actual_seed', seed)
#
#     def get_seed(self):
#         if self._prop_val('_actual_seed') is None:
#             self.set_property('_actual_seed', random.random())
#         return self._prop_val('_actual_seed')
#
#     @property
#     def randomisable(self):
#         return True
