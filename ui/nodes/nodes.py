import copy
import random
from abc import ABC, abstractmethod
from typing import Optional

from ui.id_datatypes import PropKey
from ui.nodes.node_defs import Node, PrivateNodeInfo, ResolvedProps, ResolvedRefs
from ui.nodes.prop_defs import PropValue
from ui.vis_types import Visualisable


class UnitNode(Node, ABC):
    NAME = None
    DEFAULT_NODE_INFO = None

    def __init__(self, internal_props: Optional[dict[PropKey, PropValue]] = None, add_info=None):
        self._node_info = self._default_node_info()
        super().__init__(internal_props)

    @property
    def node_info(self):
        return self._node_info

    @classmethod
    def _default_node_info(cls):
        return cls.DEFAULT_NODE_INFO


# class SelectableNode(UnitNode, ABC):
#     NAME = None
#     DEFAULT_NODE_INFO = None
#
#     def __init__(self, uid, graph_querier, internal_props=None, add_info=None):
#         self._node_info = self._default_node_info()
#         self.extracted_port_ids = []
#         super().__init__(uid, graph_querier, internal_props)
#
#     def final_compute(self, props: ResolvedProps, refs: ResolvedRefs) -> dict[PropKey, PropValue]:
#         self._remove_redundant_ports()
#         self.compute()
#
#     @abstractmethod
#     def extract_element(self, parent_group, element_id):
#         return
#
#     @abstractmethod
#     def _is_port_redundant(self, port_id):
#         pass
#
#     def _add_port(self, port_id, port_def):
#         self.node_info.port_defs[port_id] = port_def
#         self.extracted_port_ids.append(port_id)
#
#     def _remove_redundant_ports(self):
#         indices_to_remove = []
#         for i, port_id in enumerate(self.extracted_port_ids):
#             if self._is_port_redundant(port_id):
#                 del self.node_info.port_defs[port_id]
#                 self._mark_inactive_port_id(port_id)
#                 indices_to_remove.append(i)
#         indices_to_remove.reverse()
#         for i in indices_to_remove:
#             del self.extracted_port_ids[i]


class CombinationNode(Node, ABC):
    NAME = None
    SELECTIONS: list[type[Node]] = []  # To override

    def __init__(self, internal_props=None, add_info=0):
        self._selection_index = add_info
        self._node = self.selections()[add_info](internal_props)

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
    def selections(cls) -> list[type[Node]]:
        return cls.SELECTIONS

    def selection_index(self) -> int:
        return self._selection_index

    def set_selection(self, index):
        self._selection_index = index
        old_internal_props = copy.deepcopy(self.internal_props)
        self._node = self.selections()[index](internal_props=None)

        # Copy over matching existing properties
        for prop_key, old_value in old_internal_props.items():
            if prop_key in self.prop_vals:
                self.internal_props[prop_key] = old_value

    # Forwarded interface
    @property
    def base_name(self):
        return self._node.base_name

    @property
    def node_info(self):
        return self._node.node_info

    def compute(self, props: ResolvedProps, refs: ResolvedRefs) -> dict[PropKey, PropValue]:
        return self._node.compute(props, refs)

    def visualise(self, compute_results: dict[PropKey, PropValue]) -> Optional[Visualisable]:
        return self._node.visualise(compute_results)


class CustomNode(Node):
    NAME = "Custom"

    @staticmethod
    def to_custom_key(node_id, port_key):
        return f"{node_id}_{port_key}"

    @staticmethod
    def from_custom_key(custom_key):
        return tuple(custom_key.split("_", 1))  # Returns node_id, port_key

    def __init__(self, uid, graph_querier, add_info):
        super().__init__(uid, graph_querier, {})
        # Extract given information
        self._name, custom_node_def = add_info
        self.subgraph = custom_node_def.subgraph
        self.selected_ports = custom_node_def.selected_ports
        self.vis_node = self.subgraph.node(custom_node_def.vis_node)
        description = custom_node_def.description or "(No help provided)"
        # Perform set up
        self.node_topo_order = self.subgraph.get_topo_order_subgraph()
        self.randomisable_nodes_ids = [node_id for node_id, node in self.subgraph.node_map.items() if node.randomisable]
        self._randomisable = bool(self.randomisable_nodes_ids)
        self._actual_seed = None
        port_defs = {}
        for node_id, port_ids in self.selected_ports.items():
            node_port_defs = self.subgraph.node(node_id).get_port_defs()
            for port_id in port_ids:
                port_def = node_port_defs[port_id]
                port_def.optional = False
                # Replace with custom port key
                io, port_key = port_id
                port_defs[(io, CustomNode.to_custom_key(node_id, port_key))] = port_def
        # Set node info
        self._node_info = PrivateNodeInfo(
            description=description,
            port_defs=port_defs
        )

    @property
    def base_name(self):
        return self._name

    def _replace_input_nodes(self):
        # Remove existing connections
        for edge in list(self.subgraph.edges):
            _, (dst_node_id, dst_port_key) = edge
            if dst_node_id in self.selected_ports and (PortIO.INPUT, dst_port_key) in self.selected_ports[dst_node_id]:
                self.subgraph.remove_edge(*edge)
        # Get edges input to this node
        edges = self.graph_querier.edges_to_node(self.uid)
        # Get participating nodes
        source_nodes = {edge[0][0] for edge in edges}
        # Add these nodes and edges to the subgraph
        for src_node_id in source_nodes:
            self.subgraph.add_existing_node(self.graph_querier.node(src_node_id))
        for src_port_id, (_, dst_port_key) in edges:
            # Replace dest port id with original (node_id, port_key) pair
            self.subgraph.add_edge(src_port_id, CustomNode.from_custom_key(dst_port_key))

    @property
    def node_info(self):
        return self._node_info

    def compute(self):
        # Compute nodes in the subgraph
        self._replace_input_nodes()
        if self.randomisable:
            rng = random.Random(self.get_seed())
            seeds = [rng.random() for _ in range(len(self.randomisable_nodes_ids))]
        seed_i = 0
        for node_id in self.node_topo_order:
            node = self.subgraph.node(node_id)
            # Set random seed if appropriate
            if node_id in self.randomisable_nodes_ids:
                node.randomise(seeds[seed_i])
                seed_i += 1
            node.clear_compute_results()
            node.final_compute()
        # Get and set compute results
        self.compute_results = {}
        for node_id, port_ids in self.selected_ports.items():
            node = None
            for io, port_key in port_ids:
                if io == PortIO.INPUT: continue
                # We have reached an output port, get and set the compute result
                node = node or self.subgraph.node(node_id)
                self.set_compute_result(node.get_compute_result(port_key),
                                        port_key=CustomNode.to_custom_key(node_id, port_key))

    def visualise(self):
        return self.vis_node.visualise()

    # Functions needed for randomisable node

    @property
    def randomisable(self):
        return self._randomisable

    def randomise(self, seed=None):
        self._actual_seed = seed

    def get_seed(self):
        if self._actual_seed is None:
            self._actual_seed = random.random()
        return self._actual_seed
