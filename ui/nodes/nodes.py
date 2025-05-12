import copy
from abc import ABC, abstractmethod

from ui.nodes.node_defs import Node, GraphQuerier, NodeInfo
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
        self.subgraph_querier, inp_node_id, out_node_id = add_info
        # Set up node info
        inp_node: Node = self.subgraph_querier.node(inp_node_id)
        out_node: Node = self.subgraph_querier.node(out_node_id)
        inp_node_port_defs = {(io, port_key): port_def for (io, port_key), port_def in inp_node.get_port_defs().items() if io == PortIO.INPUT}
        out_node_port_defs = {(io, port_key): port_def for (io, port_key), port_def in out_node.get_port_defs().items() if io == PortIO.OUTPUT}
        port_defs = {**inp_node_port_defs, **out_node_port_defs}
        self._node_info = NodeInfo(
            description="[custom description]",
            port_defs=port_defs
        )

    @property
    def node_info(self):
        return self._node_info

    def compute(self):
        pass

    def visualise(self):
        pass