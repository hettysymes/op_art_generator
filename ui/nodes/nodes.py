import copy
from abc import ABC, abstractmethod

from ui.id_generator import gen_uid
from ui.nodes.node_defs import Node, GraphQuerier, NodeInfo, BaseNode
from ui.nodes.port_defs import PortIO


class UnitNode(Node, ABC):
    NAME = None
    DEFAULT_NODE_INFO = None

    def __init__(self, uid, graph_querier, prop_vals=None, add_info=None):
        self._node_info = self._default_node_info()
        super().__init__(uid, graph_querier, prop_vals)

    @property
    def node_info(self):
        return self._node_info

    def visualise(self):
        return self.get_compute_result('_main')

    @classmethod
    def _default_node_info(cls):
        return cls.DEFAULT_NODE_INFO

    # Functions to implement
    @abstractmethod
    def compute(self):
        return


class SelectableNode(UnitNode, ABC):
    NAME = None
    DEFAULT_NODE_INFO = None

    def __init__(self, uid, graph_querier, prop_vals=None, add_info=None):
        self._node_info = self._default_node_info()
        self.extracted_port_ids = []
        super().__init__(uid, graph_querier, prop_vals)

    def final_compute(self):
        self._remove_redundant_ports()
        self.compute()

    @abstractmethod
    def compute(self):
        pass

    @abstractmethod
    def extract_element(self, parent_group, element_id):
        return

    @abstractmethod
    def _is_port_redundant(self, port_id):
        pass

    def _add_port(self, port_id, port_def):
        self.node_info.port_defs[port_id] = port_def
        self.extracted_port_ids.append(port_id)

    def _remove_redundant_ports(self):
        indices_to_remove = []
        for i, port_id in enumerate(self.extracted_port_ids):
            if self._is_port_redundant(port_id):
                del self.node_info.port_defs[port_id]
                self._mark_inactive_port_id(port_id)
                indices_to_remove.append(i)
        indices_to_remove.reverse()
        for i in indices_to_remove:
            del self.extracted_port_ids[i]


class CombinationNode(Node, ABC):
    NAME = None
    SELECTIONS = []  # To override

    def __init__(self, uid, graph_querier, prop_vals=None, add_info=0):
        self._selection_index = add_info
        self._node = self.selections()[add_info](uid, graph_querier, prop_vals)

    def __getattr__(self, attr):
        _node = object.__getattribute__(self, "_node")
        return getattr(_node, attr)

    def __setattr__(self, name, value):
        if name in ["_node", "_selection_index"]:
            object.__setattr__(self, name, value)
        elif hasattr(type(self), name):
            # Let properties handle it
            object.__setattr__(self, name, value)
        else:
            _node = object.__getattribute__(self, "_node")
            setattr(_node, name, value)

    @classmethod
    def selections(cls):
        return cls.SELECTIONS

    def selection_index(self):
        return self._selection_index

    def set_selection(self, index):
        self._selection_index = index
        old_prop_vals = copy.deepcopy(self._node.prop_vals)
        self._node = self.selections()[index](self.uid, self.graph_querier, prop_vals=None)

        # Copy over matching existing properties
        for prop_key, old_value in old_prop_vals.items():
            if prop_key in self.prop_vals:
                self.set_property(prop_key, old_value)

    # Forwarded interface
    @property
    def base_node_name(self):
        return self._node.base_node_name

    @property
    def node_info(self):
        return self._node.node_info

    def compute(self):
        return self._node.compute()

    def visualise(self):
        return self._node.visualise()

class CustomNode(Node):
    NAME = "Custom"

    def __init__(self, uid, graph_querier, add_info):
        super().__init__(uid, graph_querier, {})
        # Extract given information
        self._name, custom_node_def = add_info
        self.subgraph = custom_node_def.subgraph
        self.inp_node_id = custom_node_def.inp_node_id
        out_node_id = custom_node_def.out_node_id
        ports_open = custom_node_def.ports_open
        # Perform set up
        self.node_topo_order = self.subgraph.get_topo_order_subgraph()
        self.input_port_keys = [port_key for (io, port_key) in ports_open if io == PortIO.INPUT]
        # Set up node info
        inp_node: Node = self.subgraph.node(self.inp_node_id)
        self.out_node: Node = self.subgraph.node(out_node_id)
        port_defs = {port_id: port_def for port_id, port_def in {**inp_node.get_port_defs(), **self.out_node.get_port_defs()}.items() if port_id in ports_open}
        self._node_info = NodeInfo(
            description="[custom description]",
            port_defs=port_defs
        )

    @property
    def base_node_name(self):
        return self._name

    def _replace_input_nodes(self):
        # Remove existing connections
        for edge in list(self.subgraph.edges):
            _, (dst_node_id, _) = edge
            if dst_node_id == self.inp_node_id:
                self.subgraph.remove_edge(*edge)
        # Get edges input to this node
        edges = self.graph_querier.edges_to_node(self.uid)
        # Get participating nodes
        source_nodes = {edge[0][0] for edge in edges}
        # Add these nodes and edges to the subgraph
        for src_node_id in source_nodes:
            self.subgraph.add_existing_node(self.graph_querier.node(src_node_id))
        for src_port_id, (_, dst_port_key) in edges:
            self.subgraph.add_edge(src_port_id, (self.inp_node_id, dst_port_key))

    @property
    def node_info(self):
        return self._node_info

    def compute(self):
        self._replace_input_nodes()
        for node_id in self.node_topo_order:
            self.subgraph.node(node_id).compute()
        self.compute_results = self.out_node.compute_results

    def visualise(self):
        return self.out_node.visualise()