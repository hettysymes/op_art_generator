import copy
import random
from abc import ABC, abstractmethod
from typing import Optional

from ui.id_datatypes import PropKey, NodeId, PortId, EdgeId, input_port
from ui.node_graph import RefId
from ui.nodes.node_defs import Node, PrivateNodeInfo, ResolvedProps, ResolvedRefs, RefQuerier
from ui.nodes.prop_defs import PropValue, PropDef, PortStatus
from ui.nodes.shape_datatypes import Group
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


class SelectableNode(UnitNode, ABC):
    NAME = None
    DEFAULT_NODE_INFO = None

    def __init__(self, internal_props: Optional[dict[PropKey, PropValue]] = None, add_info=None):
        self._node_info: PrivateNodeInfo = self._default_node_info()
        self.extracted_props: set[PropKey] = set()
        super().__init__(internal_props)

    def final_compute(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier) -> dict[PropKey, PropValue]:
        self._remove_redundant_ports(props)
        return self.compute(props, refs, ref_querier)

    @abstractmethod
    def extract_element(self, props: ResolvedProps, parent_group: Group, element_id: str) -> PropKey:
        pass

    @abstractmethod
    def _is_port_redundant(self, props: ResolvedProps, key: PropKey) -> bool:
        pass

    def _add_prop_def(self, key: PropKey, prop_def: PropDef):
        self.prop_defs[key] = prop_def
        self.extracted_props.add(key)

    def _remove_redundant_ports(self, props: ResolvedProps):
        keys_to_remove: set[PropKey] = {prop_key for prop_key in self.extracted_props if self._is_port_redundant(props, prop_key)}
        # Remove from prop_defs
        for key in keys_to_remove:
            self.prop_defs.pop(key, None)
        # Remove from extracted_props
        self.extracted_props: set[PropKey] = {key for key in self.extracted_props if key not in keys_to_remove}


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
            if prop_key in self.internal_props:
                self.internal_props[prop_key] = old_value

    # Forwarded interface
    @property
    def base_name(self):
        return self._node.base_name

    @property
    def node_info(self):
        return self._node.node_info

    def compute(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier) -> dict[PropKey, PropValue]:
        return self._node.compute(props, refs, ref_querier)

    def visualise(self, compute_results: dict[PropKey, PropValue]) -> Optional[Visualisable]:
        return self._node.visualise(compute_results)


class CustomNode(Node):
    NAME = None
    DEFAULT_NODE_INFO = None

    @staticmethod
    def to_custom_key(node_id, port_key):
        return f"{node_id}_{port_key}"

    @staticmethod
    def from_custom_key(custom_key):
        return tuple(custom_key.split("_", 1))  # Returns node_id, port_key

    @staticmethod
    def _get_new_prop_defs(prop_defs_dict: dict[NodeId, dict[PropKey, PropDef]], selected_ports: dict[NodeId, list[PortId]]) -> dict[PropKey, PropDef]:
        prop_defs: dict[PropKey, PropDef] = {}
        for node, ports in selected_ports.items():
            node_prop_defs: dict[PropKey, PropDef] = prop_defs_dict[node]
            # Collate port statuses
            # Maps to (input port status, output port status)
            port_statuses: dict[PropKey, list[PortStatus]] = {port.key: [PortStatus.FORBIDDEN, PortStatus.FORBIDDEN] for
                                                              port in ports}
            for port in ports:
                if port.is_input:
                    port_statuses[port.key][0] = PortStatus.COMPULSORY
                else:
                    port_statuses[port.key][1] = PortStatus.COMPULSORY
            # Add relevant node definitions
            for key, (inp_status, out_status) in port_statuses.items():
                prop_def = node_prop_defs[key]
                new_prop_def = PropDef(input_port_status=inp_status,
                                       output_port_status=out_status,
                                       prop_type=prop_def.prop_type,
                                       display_name=prop_def.display_name,
                                       description=prop_def.description,
                                       default_value=prop_def.default_value,
                                       auto_format=prop_def.auto_format,
                                       display_in_props=prop_def.display_in_props)
                prop_defs[CustomNode.to_custom_key(node, key)] = new_prop_def
        return prop_defs

    def __init__(self, internal_props=None, add_info=None):
        # Extract given information
        self._name, custom_node_def = add_info
        self.sub_node_manager = custom_node_def.sub_node_manager
        self.subgraph = custom_node_def.sub_node_manager.node_graph
        self.selected_ports: dict[NodeId, list[PortId]] = custom_node_def.selected_ports
        self.vis_node: NodeId = custom_node_def.vis_node
        description = custom_node_def.description or "(No help provided)"
        # Perform set up
        self.node_topo_order: list[NodeId] = self.subgraph.get_topo_order_subgraph()
        self.randomisable_nodes: list[NodeId] = [node for node in self.node_topo_order if self.sub_node_manager.node_info(node).randomisable]
        self._randomisable = bool(self.randomisable_nodes)
        self._actual_seed = None

        # Get new prop defs
        prop_defs_dict: dict[NodeId, dict[PropKey, PropDef]] = {node: self.sub_node_manager.node_info(node).prop_defs for node in self.node_topo_order}
        prop_defs: dict[PropKey, PropDef] = CustomNode._get_new_prop_defs(prop_defs_dict, self.selected_ports)

        # Set node info
        self._node_info = PrivateNodeInfo(
            description=description,
            prop_defs=prop_defs
        )
        super().__init__(internal_props)

    @property
    def base_name(self):
        return self._name

    def _replace_input_nodes(self, refs: ResolvedRefs, ref_querier: RefQuerier):
        # Remove existing connections and source nodes
        for edge in list(self.subgraph.edges):
            if edge.dst_node in self.selected_ports and edge.dst_port in self.selected_ports[edge.dst_node]:
                self.subgraph.remove_edge(edge)
                self.sub_node_manager.remove_node(edge.src_node)

        # Collate references
        refs_by_key: dict[PropKey, set[RefId]] = {}
        for key, value in refs.items():
            if isinstance(value, list):
                refs = {ref for ref in value if ref is not None}
            else:
                refs = {value} if value is not None else set()
            refs_by_key[key] = refs

        # Get edges to have and source nodes mapped to their ref
        edges_to_have: set[EdgeId] = set()
        source_nodes: dict[NodeId, RefId] = {}
        this_node: NodeId = ref_querier.uid()
        for dst_key, ref_set in refs_by_key.items():
            dst_port: PortId = input_port(node=this_node, key=dst_key)
            # Get edges connected to the above input port
            for ref in ref_set:
                src_port: PortId = ref_querier.port(ref)
                edges_to_have.add(EdgeId(src_port, dst_port))
                source_nodes[src_port.node] = ref

        # Add source nodes and edges to internal graph and node manager
        for src_node, ref in source_nodes.items():
            self.subgraph.add_node(src_node)
            self.sub_node_manager.add_node(src_node, ref_querier.node_copy(ref))
        for edge in edges_to_have:
            # Replace dest port id with original
            node, key = CustomNode.from_custom_key(edge.dst_key)
            self.subgraph.add_edge(EdgeId(edge.src_port, input_port(node=node, key=key)))

    @property
    def node_info(self):
        return self._node_info

    def compute(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier) -> dict[PropKey, PropValue]:
        # Compute nodes in the subgraph
        self._replace_input_nodes(refs, ref_querier)
        if self.randomisable:
            rng = random.Random(self.get_seed())
            seeds = [rng.random() for _ in range(len(self.randomisable_nodes))]
        seed_i = 0
        for node in self.node_topo_order:
            # Set random seed if appropriate
            if self.sub_node_manager.node_info(node).randomisable:
                self.sub_node_manager.randomise(node, seeds[seed_i])
                seed_i += 1
            # Compute
            self.sub_node_manager.compute(node)
        # Gather and return compute results
        compute_results = {}
        for node, ports in self.selected_ports.items():
            for port in ports:
                if not port.is_input:
                    compute_res: Optional[PropValue] =  self.sub_node_manager.get_compute_result(node, port.key)
                    if compute_res is not None:
                        compute_results[CustomNode.to_custom_key(node, port.key)] = compute_res
        return compute_results

    def visualise(self, *args) -> Optional[Visualisable]:
        return self.sub_node_manager.visualise(self.vis_node)

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
