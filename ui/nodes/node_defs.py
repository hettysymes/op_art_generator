import traceback
from abc import ABC, abstractmethod
from typing import Optional

from ui.id_datatypes import PropKey, NodeId, PortId, create_output_port_id, create_input_port_id, input_port, EdgeId
from ui.node_graph import NodeGraph
from ui.node_manager import NodeManager
from ui.nodes.node_implementations.visualiser import visualise_by_type
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.prop_defs import PropEntry, PropValue
from ui.nodes.shape_datatypes import Group
from ui.vis_types import ErrorFig, Visualisable


class NodeInfo:

    def __init__(self, description: str, prop_entries: Optional[dict[PropKey, PropEntry]] = None):
        self.description = description
        self.prop_entries = prop_entries if prop_entries is not None else {}


class Node(ABC):
    NAME = ""  # To override

    def __init__(self, uid: NodeId, graph_querier: NodeGraph, node_querier: NodeManager, prop_vals: Optional[dict[PropKey, PropValue]] = None):
        self.uid = uid
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

    def resolve_property(self, prop_key: PropKey) -> Optional[PropValue]:
        pass



    @classmethod
    def name(cls) -> str:
        return cls.NAME

    @property
    def base_node_name(self) -> str:
        return self.name()

    @property
    def randomisable(self) -> bool:
        return False

    # Functions to implement

    @property
    @abstractmethod
    def node_info(self) -> NodeInfo:
        pass

    @abstractmethod
    def compute(self) -> None:
        pass
