from abc import ABC, abstractmethod

from ui.nodes.node_defs import Node


class UnitNode(Node, ABC):
    NAME = None
    DEFAULT_NODE_INFO = None

    def __init__(self, uid, graph_querier, prop_vals):
        super().__init__(uid, graph_querier, prop_vals)
        self.node_info = self._default_node_info()

    def base_node_name(self):
        return self.name()

    def node_info(self):
        return self.node_info

    def visualise(self):
        return self.compute()

    @classmethod
    def _default_node_info(cls):
        return cls.DEFAULT_NODE_INFO

    # Functions to implement
    @abstractmethod
    def compute(self):
        return