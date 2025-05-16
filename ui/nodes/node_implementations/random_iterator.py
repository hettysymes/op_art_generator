# import copy
# import random
#
# from ui.nodes.node_defs import NodeInfo, PortRef
# from ui.nodes.nodes import UnitNode
# from ui.nodes.prop_defs import PortIO, PortDef, PT_List, PT_Int, PT_Hidden, PropEntry, PropType
#
# DEF_RANDOM_ITERATOR_INFO = NodeInfo(
#     description="Create a specified number of random iterations, outputting a drawing.",
#     port_defs={
#         (PortIO.INPUT, 'input'): PortDef("Random node", PT_List(input_multiple=False)),
#         (PortIO.OUTPUT, '_main'): PortDef("Random iterations", PropType())
#     },
#     prop_entries={
#         'num_iterations': PropEntry(PT_Int(min_value=1),
#                                     display_name="Number of iterations",
#                                     description="Number of random iterations of a node output to create, at least 1.",
#                                     default_value=3),
#         '_actual_seed': PropEntry(PT_Hidden())
#     }
# )
#
#
# class RandomIteratorNode(UnitNode):
#     NAME = "Random Iterator"
#     DEFAULT_NODE_INFO = DEF_RANDOM_ITERATOR_INFO
#
#     def compute(self):
#         id_elem = self._prop_val('input', get_refs=True)
#         if not id_elem:
#             # Reset output port type
#             self.get_port_defs()[(PortIO.OUTPUT, '_main')].port_type = PropType()
#             return
#         ref_id, input_value = id_elem
#         port_ref: PortRef = self._port_ref('input', ref_id)
#         src_node = self.node_graph.node(port_ref.node_id)
#         num_iterations = self._prop_val('num_iterations')
#
#         # Set output port type to be list of input type
#         self.get_port_defs()[(PortIO.OUTPUT, '_main')].port_type = PT_List(port_ref.port_def.port_type)
#
#         # If input node is not randomisable, just return the input the given number of times
#         if not src_node.randomisable:
#             self.set_compute_result([input_value for _ in range(num_iterations)])
#             return
#
#         # Get random seeds
#         rng = random.Random(self.get_seed())
#         seeds = [rng.random() for _ in range(num_iterations)]
#
#         # Calculate and set random compute result
#         outputs = []
#         for seed in seeds:
#             random_node = copy.deepcopy(src_node)
#             random_node.randomise(seed)
#             random_node.clear_compute_results()
#             random_node.final_compute()
#             outputs.append(random_node.get_compute_result(port_ref.port_key))
#         self.set_compute_result(outputs)
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
