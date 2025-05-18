import copy
import traceback
from abc import ABC, abstractmethod
from typing import Optional

from ui.id_datatypes import PropKey, NodeId, PortId, input_port, EdgeId
from ui.node_graph import NodeGraph, RefId
from ui.nodes.node_implementations.visualiser import visualise_by_type
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.prop_defs import PropDef, PropValue, PropType, PT_Scalar, PT_List, List, PortRefTableEntry, \
    PT_PointsHolder, LineRef
from ui.nodes.shape_datatypes import Group
from ui.vis_types import ErrorFig, Visualisable

type ResolvedProps = dict[PropKey, list[PropValue] | PropValue]
type ResolvedRefs = dict[PropKey, list[Optional[RefId]] | Optional[RefId]]


class PrivateNodeInfo:

    def __init__(self, description: str, prop_defs: Optional[dict[PropKey, PropDef]] = None):
        self.description = description
        self.prop_defs: dict[PropKey, PropDef] = prop_defs if prop_defs is not None else {}

class Node(ABC):
    NAME = ""  # To override

    def __init__(self, internal_props: Optional[dict[PropKey, PropValue]] = None):
        self.internal_props: dict[PropKey, PropValue] = self.default_internal_props() if internal_props is None else internal_props

    def default_internal_props(self):
        default_props: dict[PropKey, PropValue] = {}
        prop_defs: dict[PropKey, PropDef] = self.prop_defs
        for key, prop_def in prop_defs.items():
            if prop_def.default_value is not None:
                default_props[key] = prop_def.default_value
        return default_props

    def final_compute(self, props: ResolvedProps, refs: ResolvedRefs) -> dict[PropKey, PropValue]:
        return self.compute(props, refs)

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
    def compute(self, props: ResolvedProps, refs: ResolvedRefs) -> dict[PropKey, PropValue]:
        pass

class RuntimeNode:
    def __init__(self, uid: NodeId, graph_querier: NodeGraph, node_querier, node: Node):
        self.uid = uid
        self.graph_querier = graph_querier
        self.node_querier = node_querier
        self.compute_results: dict[PropKey, PropValue] = {}
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

    def compute(self) -> None:
        self.compute_results = self.node.final_compute(*self.resolve_properties())

    def resolve_properties(self) -> tuple[ResolvedProps, ResolvedRefs]:
        prop_vals: ResolvedProps = {}
        refs: ResolvedRefs = {}
        for key in self.node.prop_defs:
            result = self.get_property(key)
            if result is not None:
                prop_vals[key], refs[key] = result # Set
        return prop_vals, refs

    def get_property(self, prop_key: PropKey) -> (
        None                                                    # No return if no property could be resolved
        | tuple[list[PropValue], list[Optional[RefId]]]         # List if input port type inputs from multiple nodes
        | tuple[PropValue, Optional[RefId]]                     # Single value otherwise
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
            existing_refs: set[RefId] = {ref_entry.ref for ref_entry in prop_value if isinstance(ref_entry, PortRefTableEntry)}
            for comp_result, ref in zip(results, refs):
                assert comp_result.type.is_compatible_with(prop_value.type)
                if ref in existing_refs:
                    existing_refs.discard(ref)
                else:
                    for cr in comp_result:
                        if isinstance(cr.type, PT_PointsHolder):
                            class_entry = LineRef
                        else:
                            class_entry = PortRefTableEntry
                        prop_value.append(class_entry(ref=ref, data=cr, deletable=False))
            # Remove no longer existing refs
            idxs_to_remove: list[int] = []
            for i, ref_entry in enumerate(prop_value):
                if isinstance(ref_entry, PortRefTableEntry) and ref_entry.ref in existing_refs:
                    idxs_to_remove.append(i)
            idxs_to_remove.reverse()
            for i in idxs_to_remove:
                prop_value.delete(i)
            return prop_value, None

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
        return self.compute_results.get(key)
