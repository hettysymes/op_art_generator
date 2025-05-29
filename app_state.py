from dataclasses import dataclass
from typing import Optional

from id_datatypes import NodeId, PortId, PropKey
from node_manager import NodeManager


# State classes
@dataclass
class NodeState:
    node: NodeId
    ports_open: list[PortId]
    pos: tuple[float, float]
    svg_size: tuple[float, float]


@dataclass(frozen=True)
class CustomNodeDef:
    sub_node_manager: NodeManager
    selected_ports: dict[NodeId, list[PortId]]
    custom_names: dict[tuple[NodeId, PropKey], str]
    vis_node: NodeId
    description: Optional[str] = None


@dataclass(frozen=True)
class AppState:
    view_pos: tuple[float, float]
    zoom: float
    node_states: list[NodeState]
    node_manager: NodeManager
    custom_node_defs: dict[str, CustomNodeDef]
    next_node_id: int
