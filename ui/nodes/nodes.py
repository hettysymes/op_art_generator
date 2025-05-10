from abc import ABC, abstractmethod

from ui.nodes.node_defs import Node


class UnitNode(Node, ABC):
    NAME = None
    DEFAULT_NODE_INFO = None

    def __init__(self, uid, graph_querier, prop_vals=None, add_info=None):
        self.node_info = self._default_node_info()
        super().__init__(uid, graph_querier, prop_vals)

    def base_node_name(self):
        return self.name()

    def get_node_info(self):
        return self.node_info

    def visualise(self):
        return self.compute()

    @classmethod
    def _default_node_info(cls):
        return cls.DEFAULT_NODE_INFO

    # Functions to implement
    @abstractmethod
    def compute(self, out_port_key='_main'):
        return

class SelectableNode(UnitNode, ABC):
    NAME = None
    DEFAULT_NODE_INFO = None

    @abstractmethod
    def compute(self, out_port_key='_main'):
        return

    @abstractmethod
    def extract_element(self, parent_group, element_id):
        return


class CombinationNode(Node, ABC):
    NAME = None
    SELECTIONS = []  # To override

    # Additional info (add_info) is the selection index
    def __init__(self, uid, graph_querier, prop_vals=None, add_info=0):
        self._selection_index = add_info
        self._node = self.selections()[add_info](uid, graph_querier, prop_vals)
        super().__init__(self._node.uid, self._node.graph_querier, self._node.prop_vals)

    @classmethod
    def selections(cls):
        return cls.SELECTIONS

    def selection_index(self):
        return self._selection_index

    def set_selection(self, index):
        self._selection_index = index
        # Set new node with default properties
        self._node = self.selections()[index](self.uid, self.graph_querier, prop_vals=None)
        # Keep shared properties e.g. fill colour
        for prop_key, old_value in self.prop_vals.items():
            if prop_key in self._node.prop_vals:
                self._node.set_property(prop_key, old_value)
        # Set reference to node prop vals in this node
        self.prop_vals = self._node.prop_vals

    def base_node_name(self):
        return self._node.base_node_name()

    def get_node_info(self):
        return self._node.get_node_info()

    def compute(self, out_port_key='_main'):
        return self._node.compute(out_port_key)

    def visualise(self):
        return self._node.visualise()
