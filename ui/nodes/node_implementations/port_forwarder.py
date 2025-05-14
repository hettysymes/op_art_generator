from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_implementations.port_ref_table_handler import handle_port_ref_table
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Element, PT_List, PT_ElemRefTable, PropEntry, PortType
from ui.nodes.shape_datatypes import Group

DEF_PORT_FORWARDER = NodeInfo(
    description="Forward a port to multiple ports. Useful when making custom nodes.",
    port_defs={
        (PortIO.INPUT, 'input'): PortDef("Input", PortType()),
        (PortIO.OUTPUT, '_main'): PortDef("Output", PortType())
    }
)


class PortForwarderNode(UnitNode):
    NAME = "Port Forwarder"
    DEFAULT_NODE_INFO = DEF_PORT_FORWARDER

    def compute(self):
        inp_key = 'input'
        input_srcs = self.graph_querier._input_sources(self.uid, inp_key)
        if input_srcs:
            # Input node exists, get output type of connected key
            src_node_id, src_port_key = next(iter(input_srcs))
            set_type = self.graph_querier.node(src_node_id).get_port_defs()[(PortIO.OUTPUT, src_port_key)].port_type
            # Set compute result
            self.set_compute_result(self._port_input(inp_key)[0])
        else:
            # No input node
            set_type = PortType()
        # Update output port type
        self.get_port_defs()[(PortIO.OUTPUT, '_main')].port_type = set_type