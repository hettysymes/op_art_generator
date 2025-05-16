# from ui.nodes.node_defs import NodeInfo
# from ui.nodes.nodes import UnitNode
# from ui.nodes.prop_defs import PortIO, PortDef, PropType
#
# DEF_PORT_FORWARDER_INFO = NodeInfo(
#     description="Forward a port to multiple ports. Useful when making custom nodes.",
#     port_defs={
#         (PortIO.INPUT, 'input'): PortDef("Input", PropType()),
#         (PortIO.OUTPUT, '_main'): PortDef("Output", PropType())
#     }
# )
#
#
# class PortForwarderNode(UnitNode):
#     NAME = "Port Forwarder"
#     DEFAULT_NODE_INFO = DEF_PORT_FORWARDER_INFO
#
#     def compute(self):
#         inp_key = 'input'
#         input_srcs = self.node_graph.conn_src_ports(self.uid, inp_key)
#         if input_srcs:
#             # Input node exists, get output type of connected key
#             src_node_id, src_port_key = next(iter(input_srcs))
#             set_type = self.node_graph.node(src_node_id).get_port_defs()[(PortIO.OUTPUT, src_port_key)].port_type
#             # Set compute result
#             self.set_compute_result(self._port_input(inp_key)[0])
#         else:
#             # No input node
#             set_type = PropType()
#         # Update output port type
#         self.get_port_defs()[(PortIO.OUTPUT, '_main')].port_type = set_type
