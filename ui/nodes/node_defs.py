import copy
import traceback
from abc import ABC, abstractmethod
from typing import Optional, cast

from ui.id_datatypes import PropKey, NodeId, PortId, input_port, EdgeId
from ui.node_graph import NodeGraph, RefId
from ui.nodes.node_implementations.visualiser import visualise_by_type
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.prop_defs import PropDef, PropValue, PropType, PT_Scalar, PT_List, List, PortRefTableEntry, \
    PT_PointsHolder, LineRef, PT_ElementHolder, ElementRef, PT_ColourHolder, ColourRef
from ui.nodes.shape_datatypes import Group
from ui.vis_types import ErrorFig, Visualisable

type ResolvedProps = dict[PropKey, list[PropValue] | PropValue]
type ResolvedRefs = dict[PropKey, list[Optional[RefId]] | Optional[RefId]]


class RefQuerier:

    def __init__(self, uid, node_querier, graph_querier):
        self._uid = uid
        self._node_querier = node_querier
        self._graph_querier = graph_querier

    def node_info(self, ref: RefId):
        return self._node_querier.node_info(self.port(ref).node)

    def node_copy(self, ref: RefId):
        node: NodeId = self.port(ref).node
        return self._node_querier.get_node_copies({node})[node]

    def get_compute_inputs(self, ref: RefId):
        return self._node_querier.get_compute_inputs(self.port(ref).node)

    def get_compute_results(self, ref: RefId):
        return self._node_querier.get_compute_results(self.port(ref).node)

    def get_compute_result(self, ref: RefId):
        port: PortId = self.port(ref)
        return self._node_querier.get_compute_result(port.node, port.key)

    def port(self, ref: RefId) -> PortId:
        return self._graph_querier.query_ref(self._uid, ref)

    @property
    def uid(self) -> NodeId:
        return self._uid


class PrivateNodeInfo:

    def __init__(self, description: str, prop_defs: Optional[dict[PropKey, PropDef]] = None):
        self.description = description
        self.prop_defs: dict[PropKey, PropDef] = prop_defs if prop_defs is not None else {}


class Node(ABC):
    NAME = ""  # To override

    def __init__(self, internal_props: Optional[dict[PropKey, PropValue]] = None):
        self.internal_props: dict[
            PropKey, PropValue] = self.default_internal_props() if internal_props is None else internal_props

    def default_internal_props(self):
        default_props: dict[PropKey, PropValue] = {}
        prop_defs: dict[PropKey, PropDef] = self.prop_defs
        for key, prop_def in prop_defs.items():
            if prop_def.default_value is not None:
                default_props[key] = prop_def.default_value
        return default_props

    def final_compute(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier) -> dict[
        PropKey, PropValue]:
        return self.compute(props, refs, ref_querier)

    def visualise(self, compute_results: dict[PropKey, PropValue]) -> Optional[Visualisable]:
        try:
            value: PropValue = compute_results['_main']
            return visualise_by_type(value, value.type)
        except:
            return None

    @classmethod
    def name(cls) -> str:
        return cls.NAME

    @property
    def base_name(self) -> str:
        return self.name()

    @property
    def randomisable(self) -> bool:
        return False

    @property
    def description(self) -> str:
        return self.node_info.description

    @property
    def prop_defs(self) -> dict[PropKey, PropDef]:
        return self.node_info.prop_defs

    # Functions to implement

    @property
    @abstractmethod
    def node_info(self) -> PrivateNodeInfo:
        pass

    @abstractmethod
    def compute(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier) -> dict[PropKey, PropValue]:
        pass


class RuntimeNode:
    def __init__(self, uid: NodeId, graph_querier: NodeGraph, node_querier, node: Node, compute_results=None):
        self.uid = uid
        self.graph_querier = graph_querier
        self.node_querier = node_querier
        self.compute_results: dict[PropKey, PropValue] = {} if compute_results is None else compute_results
        self.node: Node = node

    def visualise(self) -> Visualisable:
        # Catch exception if raised
        try:
            # Recompute results
            self.compute()
            # Obtain visualisation
            vis = self.node.visualise(self.compute_results)
        except NodeInputException as e:
            vis = ErrorFig(e.title, e.message)
        except Exception as e:
            vis = ErrorFig("Unknown Exception", str(e))
            traceback.print_exc()
        if not vis:
            # No visualisation, return blank canvas
            vis = Group(debug_info="Blank Canvas")
        return vis

    def get_compute_inputs(self) -> tuple[ResolvedProps, ResolvedRefs, RefQuerier]:
        props, refs = self.resolve_properties()
        return props, refs, RefQuerier(self.uid, self.node_querier, self.graph_querier)

    def compute(self) -> None:
        self.compute_results = self.node.final_compute(*self.get_compute_inputs())

    def extract_element(self, parent_group: Group, element_id: str) -> PropKey:
        return self.node.extract_element(self.resolve_properties()[0], parent_group, element_id)

    def resolve_properties(self) -> tuple[ResolvedProps, ResolvedRefs]:
        prop_vals: ResolvedProps = {}
        refs: ResolvedRefs = {}
        for key in self.node.prop_defs:
            result = self.get_property(key)
            if result is not None:
                prop_vals[key], refs[key] = result  # Set
        return prop_vals, refs

    def get_property(self, prop_key: PropKey) -> (
            None  # No return if no property could be resolved
            | tuple[List, list[Optional[RefId]]]  # List if input port type inputs from multiple nodes
            | tuple[PropValue, Optional[RefId]]  # Single value otherwise
    ):
        prop_type: PropType = self.node.prop_defs[prop_key].prop_type
        incoming_edges: set[EdgeId] = self.graph_querier.incoming_edges(input_port(self.uid, prop_key))
        results: list[PropValue] = []
        refs: list[Optional[RefId]] = []
        for edge in incoming_edges:
            comp_result: Optional[PropValue] = self.node_querier.resolve_property(edge.src_port, prop_type)
            if comp_result is not None:
                ref: RefId = self.graph_querier.get_ref(self.uid, edge.src_port)
                # Compute result is not None, add both compute result and reference
                results.append(comp_result)
                refs.append(ref)

        if isinstance(prop_type, PT_List) and prop_type.input_multiple:
            # Port input UPDATES the internal state
            prop_value: List = self.node.internal_props.get(prop_key)
            assert isinstance(prop_value, List)
            ref_result_map: dict[RefId, List[PropValue]] = {ref: comp_result for ref, comp_result in zip(refs, results)}
            new_prop_value: List = List(prop_value.item_type)
            # Update existing references
            updated_refs: set[RefId] = set()
            ret_refs: list[Optional[RefId]] = []  # References to return
            i = 0
            while i < len(prop_value):
                curr_prop = prop_value[i]
                if isinstance(curr_prop, PortRefTableEntry):
                    old_group_len: int = cast(PortRefTableEntry, prop_value[i]).group_idx[1]
                    if curr_prop.ref in ref_result_map:
                        # Update with new group length
                        updated_refs.add(curr_prop.ref)
                        results_for_ref = ref_result_map[curr_prop.ref]
                        new_group_len: int = len(results_for_ref)
                        for res_idx, compute_result in enumerate(results_for_ref):
                            new_ref_entry: PortRefTableEntry = copy.deepcopy(curr_prop)
                            new_ref_entry.data = compute_result
                            new_ref_entry.group_idx = (res_idx + 1, new_group_len)
                            # Add updated entry
                            new_prop_value.append(new_ref_entry)
                        ret_refs.extend([curr_prop.ref] * new_group_len)
                    # Whole group has been processed
                    i += old_group_len
                else:
                    new_prop_value.append(curr_prop)
                    ret_refs.append(None)
                    i += 1
            # Add new references
            new_refs: set[RefId] = set(ref_result_map.keys()) - updated_refs
            for ref in new_refs:
                group_len: int = len(ref_result_map[ref])
                for i, compute_result in enumerate(ref_result_map[ref]):
                    if isinstance(prop_value.item_type, PT_PointsHolder):
                        class_entry = LineRef
                    elif isinstance(prop_value.item_type, PT_ElementHolder):
                        class_entry = ElementRef
                    elif isinstance(prop_value.item_type, PT_ColourHolder):
                        class_entry = ColourRef
                    else:
                        class_entry = PortRefTableEntry
                    new_prop_value.append(
                        class_entry(ref=ref, data=compute_result, group_idx=(i + 1, group_len), deletable=False))
                ret_refs.extend([ref] * group_len)
            assert len(new_prop_value) == len(ret_refs)
            # Set this as new property
            self.node.internal_props[prop_key] = new_prop_value
            return new_prop_value, ret_refs

        elif not results:
            # No incoming edge results, default to internal property value if it exists
            prop_value: Optional[PropValue] = self.node.internal_props.get(prop_key)
            if prop_value is None:
                # No value could be resolved anywhere
                return None
            else:
                results = [prop_value]
                refs = [None]
        if isinstance(prop_type, PT_Scalar) or (isinstance(prop_type, PT_List) and not prop_type.input_multiple):
            # We know there will be at most one result, so just return the first one
            return results[0], refs[0]
        # Port input
        return results, refs

    def get_compute_result(self, key: PropKey) -> Optional[PropValue]:
        if key in self.compute_results:
            return self.compute_results[key]
        # Forwarding an internal property
        return self.node.internal_props.get(key)
