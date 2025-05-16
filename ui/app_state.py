from dataclasses import dataclass
from typing import Optional

from ui.id_datatypes import NodeId, PortId
from ui.node_graph import NodeGraph


# State classes
@dataclass
class NodeState:
    node_id: NodeId
    ports_open: list[PortId]
    pos: tuple[float, float]
    svg_size: tuple[float, float]


@dataclass(frozen=True)
class CustomNodeDef:
    subgraph: NodeGraph
    selected_ports: dict[NodeId, list[PortId]]
    vis_node_id: NodeId
    description: Optional[str] = None


@dataclass(frozen=True)
class AppState:
    view_pos: tuple[float, float]
    zoom: float
    node_states: list[NodeState]
    node_graph: NodeGraph
    custom_node_defs: dict[str, CustomNodeDef]
