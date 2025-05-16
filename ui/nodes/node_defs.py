import traceback
from abc import ABC, abstractmethod
from typing import Optional

from ui.id_datatypes import PropKey, NodeId, PortId, input_port, EdgeId
from ui.node_graph import NodeGraph, RefId
from ui.node_manager import NodeManager
from ui.nodes.node_implementations.visualiser import visualise_by_type
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.prop_defs import PropDef, PropValue, PropType, PT_Scalar, PT_List
from ui.nodes.shape_datatypes import Group
from ui.vis_types import ErrorFig, Visualisable


class PrivateNodeInfo:

    def __init__(self, description: str, prop_defs: Optional[dict[PropKey, PropDef]] = None):
        self.description = description
        self.prop_defs: dict[PropKey, PropDef] = prop_defs if prop_defs is not None else {}


class Node(ABC):
    NAME = ""  # To override

    def __init__(self, graph_querier: NodeGraph, node_querier: NodeManager, prop_vals: Optional[dict[PropKey, PropValue]] = None):
        self.graph_querier = graph_querier
        self.node_querier = node_querier
        self.prop_vals = prop_vals
        self.compute_results: dict[PropKey, PropValue] = {}

    def safe_visualise(self) -> Visualisable:
        # Catch exception if raised
        try:
            # Recompute results
            self.clear_compute_results()
            self.final_compute()
            # Obtain visualisation
            vis = self.visualise()
        except NodeInputException as e:
            if e.node_id == self.uid:
                msg = str(e.message)
            else:
                msg = f"Error further up pipeline (id {e.node_id})."
            vis = ErrorFig(e.title, msg)
        except Exception as e:
            vis = ErrorFig("Unknown Exception", str(e))
            traceback.print_exc()
        if not vis:
            # No visualisation, return blank canvas
            vis = Group(debug_info="Blank Canvas")
        return vis

    def clear_compute_results(self) -> "Node":
        self.compute_results.clear()
        return self

    def get_compute_result(self, key: PropKey = '_main') -> Optional[PropValue]:
        return self.compute_results.get(key)

    def set_compute_result(self, value: PropValue, key: PropKey = '_main') -> None:
        self.compute_results[key] = value

    def final_compute(self) -> None:
        return self.compute()

    def visualise(self) -> Optional[Visualisable]:
        try:
            value: PropValue = self.get_compute_result()
            return visualise_by_type(value, value.type)
        except:
            return None

    def get_property(self, prop_key: PropKey, get_refs: bool = False) -> (
        None
        | list[tuple[RefId, PropValue]]
        | list[PropValue]
        | tuple[RefId, PropValue]
        | PropValue
    ):
        prop_type: PropType = self.prop_defs[prop_key].prop_type
        incoming_edges: set[EdgeId] = self.graph_querier.incoming_edges(input_port(self.uid, prop_key))
        results: list[tuple[RefId, PropValue]] | list[PropValue] = []
        for edge in incoming_edges:
            comp_result: Optional[PropValue] = self.node_querier.resolve_property(edge.src_port, prop_type)
            if comp_result:
                if get_refs:
                    ref: RefId = self.graph_querier.get_ref_id(self.uid, edge.src_port)
                    results.append((ref, comp_result))
                else:
                    results.append(comp_result)
        if not results:
            # No incoming edge results, default to internal property value if it exists
            prop_value: Optional[PropValue] = self.prop_vals.get(prop_key)
            if prop_value:
                results = [prop_value]
            else:
                # No value could be resolved anywhere
                return None
        if isinstance(prop_type, PT_Scalar) or (isinstance(prop_type, PT_List) and not prop_type.input_multiple):
            # We know there will be at most one result, so just return the first one
            return results[0]
        return results


    @classmethod
    def name(cls) -> str:
        return cls.NAME

    @property
    def base_node_name(self) -> str:
        return self.name()

    @property
    def randomisable(self) -> bool:
        return False

    @property
    def description(self):
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
    def compute(self) -> None:
        pass
