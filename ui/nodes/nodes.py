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

class CombinationNode(Node, ABC):
    NAME = None
    SELECTIONS = [] # To override

    def __init__(self, uid, graph_querier, prop_vals=None, add_info=0):
        self.selection_index = add_info
        self._node = self._cur_node_class()(uid, graph_querier, prop_vals)
        super().__init__(self._node.uid, self._node.graph_querier, self._node.prop_vals)

    @classmethod
    def selections(cls):
        return cls.SELECTIONS

    def _cur_node_class(self):
        return self.selections()[self.selection_index]

    def base_node_name(self):
        return self._node.base_node_name()

    def get_node_info(self):
        return self._node.get_node_info()

    def compute(self, out_port_key='_main'):
        return self._node.compute(out_port_key)

    def visualise(self):
        return self._node.visualise()