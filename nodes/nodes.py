import copy
import random
from abc import ABC, abstractmethod
from typing import Optional, cast

from id_datatypes import PropKey, NodeId, PortId, EdgeId, input_port
from node_graph import RefId
from nodes.node_defs import Node, PrivateNodeInfo, ResolvedProps, ResolvedRefs, RefQuerier, PropDef, PortStatus, \
    NodeCategory, DisplayStatus
from nodes.prop_types import PT_Int, PT_Number
from nodes.prop_values import PropValue, Float
from nodes.shape_datatypes import Group
from vis_types import Visualisable


class UnitNode(Node, ABC):
    NAME = None
    NODE_CATEGORY = None
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
    NODE_CATEGORY = None
    DEFAULT_NODE_INFO = None

    def __init__(self, internal_props: Optional[dict[PropKey, PropValue]] = None, add_info=None):
        self._node_info: PrivateNodeInfo = self._default_node_info()
        self.extracted_props: set[PropKey] = set()
        super().__init__(internal_props)

    def final_compute(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier) -> dict[
        PropKey, PropValue]:
        self._remove_redundant_ports(props)
        return self.compute(props, refs, ref_querier)

    @abstractmethod
    def extract_element(self, props: ResolvedProps, parent_group: Group, element_id: str) -> PropKey:
        pass

    @abstractmethod
    def _is_port_redundant(self, props: ResolvedProps, key: PropKey) -> bool:
        pass

    def _add_prop_def(self, key: PropKey, prop_def: PropDef) -> None:
        self.prop_defs[key] = prop_def
        self.extracted_props.add(key)

    def _remove_redundant_ports(self, props: ResolvedProps):
        keys_to_remove: set[PropKey] = {prop_key for prop_key in self.extracted_props if
                                        self._is_port_redundant(props, prop_key)}
        # Remove from prop_defs
        for key in keys_to_remove:
            self.prop_defs.pop(key, None)
        # Remove from extracted_props
        self.extracted_props: set[PropKey] = {key for key in self.extracted_props if key not in keys_to_remove}


class RandomisableNode(UnitNode, ABC):

    def __init__(self, internal_props: Optional[dict[PropKey, PropValue]] = None, add_info=None):
        self._node_info: PrivateNodeInfo = self._default_node_info()
        self._node_info.prop_defs['seed'] = PropDef(
            prop_type=PT_Int(min_value=0),
            display_name="Random seed",
            description="Random seed used."
        )
        super().__init__(internal_props)

    def randomise(self, seed=None):
        min_seed: int = cast(PT_Int, self.prop_defs['seed'].prop_type).min_value
        max_seed: int = cast(PT_Int, self.prop_defs['seed'].prop_type).max_value
        set_seed = seed if seed is not None else random.randint(min_seed, max_seed)
        self.internal_props['seed'] = set_seed
        return set_seed

    def get_seed(self):
        return self.internal_props['seed']

    @property
    def randomisable(self):
        return True

    def get_random_obj(self, seed=None) -> random.Random:
        if seed is None:
            seed = self.randomise()
        return random.Random(seed)


class AnimatableNode(UnitNode, ABC):
    def __init__(self, internal_props: Optional[dict[PropKey, PropValue]] = None, add_info=None):
        self._node_info: PrivateNodeInfo = self._default_node_info()
        self._node_info.prop_defs['jump_time'] = PropDef(
            prop_type=PT_Number(min_value=10),
            display_name="Time between animate change / ms",
            default_value=Float(200)
        )
        self._time_left = 0  # In milliseconds
        self._playing = False
        self._reanimate_on_compute = False
        super().__init__(internal_props)

    @property
    def animatable(self) -> bool:
        return True

    @property
    def playing(self) -> bool:
        return self._playing

    def tick_reanimate(self) -> bool:
        reanimate = self._reanimate_on_compute
        if reanimate:
            self._reanimate_on_compute = False
        return reanimate

    def reanimate(self, time: float) -> bool:
        # time is time in milliseconds that has passed
        # Returns True if it moved to the next animation step
        assert self.playing
        self._time_left -= time
        if self._time_left <= 0:
            # Reset time left
            self._time_left: float = self.internal_props['jump_time']  # Time in milliseconds
            self._reanimate_on_compute = True
        else:
            self._reanimate_on_compute = False
        return self._reanimate_on_compute

    def toggle_play(self) -> None:
        self._playing = not self._playing


class CombinationNode(Node, ABC):
    NAME = None
    NODE_CATEGORY = None
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
    NAME = "Custom"
    NODE_CATEGORY = NodeCategory.UNKNOWN
    DEFAULT_NODE_INFO = None

    @staticmethod
    def to_custom_key(node_id, port_key) -> PropKey:
        return f"{node_id.value}_{port_key}"

    @staticmethod
    def from_custom_key(custom_key) -> tuple[NodeId, PropKey]:
        node_str, key = custom_key.split("_", 1)
        return NodeId(int(node_str)), key  # Returns node id, port_key

    @staticmethod
    def _get_new_prop_defs(prop_defs_dict: dict[NodeId, dict[PropKey, PropDef]],
                           selected_ports: dict[NodeId, list[PortId]],
                           custom_names: dict[tuple[NodeId, PropKey], str]) -> dict[PropKey, PropDef]:
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
                                       display_name=custom_names[(node, key)],
                                       description=prop_def.description,
                                       default_value=prop_def.default_value,
                                       auto_format=prop_def.auto_format,
                                       display_status=prop_def.display_status)
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
        # Randomisable nodes
        self.randomisable_nodes: list[NodeId] = [node for node in self.node_topo_order if
                                                 self.sub_node_manager.node_info(node).randomisable]
        self._randomisable = bool(self.randomisable_nodes)
        # Animatable nodes
        self.animatable_nodes: list[NodeId] = [node for node in self.node_topo_order if
                                               self.sub_node_manager.node_info(node).animatable]
        self._animatable = bool(self.animatable_nodes)
        self._playing = None
        self.set_playing(False)

        # Get new prop defs
        prop_defs_dict: dict[NodeId, dict[PropKey, PropDef]] = {node: self.sub_node_manager.node_info(node).prop_defs
                                                                for node in self.node_topo_order}
        prop_defs: dict[PropKey, PropDef] = CustomNode._get_new_prop_defs(prop_defs_dict, self.selected_ports,
                                                                          custom_node_def.custom_names)

        # Add seed property if randomisable
        if self._randomisable:
            prop_defs['seed'] = PropDef(
                prop_type=PT_Int(min_value=0),
                display_name="Random seed",
                description="Random seed used.",
                input_port_status=PortStatus.FORBIDDEN,
                output_port_status=PortStatus.FORBIDDEN
            )

        if self._animatable:
            prop_defs['speed'] = PropDef(
                prop_type=PT_Number(min_value=0.001, max_value=10),
                display_name="Animation speed",
                description="Relative playback speed of the animation (1 = normal speed, 2 = twice as fast, 0.5 = half speed).",
                input_port_status=PortStatus.FORBIDDEN,
                output_port_status=PortStatus.FORBIDDEN,
                default_value=Float(1)
            )

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
        this_node: NodeId = ref_querier.uid
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
            self.sub_node_manager.add_node(src_node, ref_querier.node_copy(ref),
                                           compute_results=ref_querier.get_compute_results(ref))
        for edge in edges_to_have:
            # Replace dest port id with original
            node, key = CustomNode.from_custom_key(edge.dst_key)
            self.subgraph.add_edge(EdgeId(edge.src_port, input_port(node=node, key=key)))

    def _update_internal_props(self, props):
        for prop_key, prop_val in props.items():
            try:
                node, key = CustomNode.from_custom_key(prop_key)
                self.sub_node_manager.set_internal_property(node, key, prop_val)
            except ValueError:
                pass

    @property
    def node_info(self):
        return self._node_info

    def compute(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier) -> dict[PropKey, PropValue]:
        # Compute nodes in the subgraph
        self._replace_input_nodes(refs, ref_querier)
        self._update_internal_props(props)
        if self.randomisable:
            if props.get('seed') is None:
                self.randomise()
            rng = random.Random(props.get('seed'))
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
                    compute_res: Optional[PropValue] = self.sub_node_manager.get_compute_result(node, port.key)
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
        min_seed: int = cast(PT_Int, self.prop_defs['seed'].prop_type).min_value
        max_seed: int = cast(PT_Int, self.prop_defs['seed'].prop_type).max_value
        self.internal_props['seed'] = seed if seed is not None else random.randint(min_seed, max_seed)

    def get_seed(self):
        return self.internal_props['seed']

    # Functions needed for animatable node
    def set_playing(self, is_playing: bool):
        for node in self.animatable_nodes:
            if self.sub_node_manager.is_playing(node) != is_playing:
                self.sub_node_manager.toggle_play(node)
        self._playing = is_playing

    @property
    def animatable(self) -> bool:
        return self._animatable

    @property
    def playing(self) -> bool:
        return self._playing

    def reanimate(self, time: float) -> bool:
        # time is time in milliseconds that has passed
        # Returns True if it moved to the next animation step
        assert self.playing
        rel_time: float = self.internal_props['speed'] * time
        update: bool = False
        for node in self.animatable_nodes:
            update = update or self.sub_node_manager.reanimate(node, rel_time)
        return update

    def toggle_play(self) -> None:
        self.set_playing(not self._playing)
