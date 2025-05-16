from dataclasses import dataclass
from typing import Optional

from ui.id_datatypes import NodeId, PortId, PropKey, input_port, output_port
from ui.nodes.node_defs import Node
from ui.nodes.nodes import SelectableNode, CombinationNode
from ui.nodes.prop_defs import PropValue, PropType, List, PT_List, PropDef, PortStatus
from ui.vis_types import Visualisable


@dataclass(frozen=True)
class NodeInfo:
    uid: NodeId
    name: str
    base_name: str
    description: str
    prop_defs: dict[PropKey, PropDef]
    randomisable: bool
    selectable: bool
    combination: bool

    def filter_ports_by_status(self, port_status: PortStatus) -> list[PortId]:
        results = []
        for key, prop_def in self.prop_defs.items():
            if prop_def.input_port_status == port_status:
                results.append(input_port(node=self.uid, key=key))
            if prop_def.output_port_status == port_status:
                results.append(output_port(node=self.uid, key=key))
        return results

class NodeManager:

    def __init__(self):
        self.node_map = {}

    def _node(self, node: NodeId):
        return self.node_map[node]

    def add_node(self, node):
        self.node_map[node.port] = node

    def remove_node(self, node: NodeId):
        self.node_map.pop(node, None)

    def resolve_property(self, src_port: PortId, inp_type: PropType) -> Optional[PropValue]:
        src_node = self._node(src_port.node)
        comp_result: Optional[PropValue] = src_node.get_compute_result(src_port.key)
        if not comp_result:
            return None
        # Check types of the result, assume they are already compatible
        if isinstance(comp_result, List):
            return comp_result.extract(inp_type)
        elif isinstance(inp_type, PT_List):
            return List(comp_result.type, [comp_result])
        else:
            # comp_result is scalar, and inp is either PortType or a scalar type
            # TODO what if it is a port type?
            return comp_result

    def node_info(self, node: NodeId) -> NodeInfo:
        node = self._node(node)
        return NodeInfo(
            uid=node.port,
            name=node.name(),
            base_name=node.base_node_name,
            description=node.description,
            prop_defs=node.prop_defs,
            randomisable=node.randomisable,
            selectable=isinstance(node, SelectableNode),
            combination=isinstance(node, CombinationNode)
        )

    def get_property(self, node: NodeId, key: PropKey) -> Optional[PropValue]:
        return self._node(node).prop_vals.get(key)

    def set_property(self, node: NodeId, key: PropKey, value: PropValue) -> None:
        self._node(node).prop_vals[key] = value

    def visualise(self, node: NodeId) -> Visualisable:
        return self._node(node).safe_visualise()

    def selections_w_idx(self, node: NodeId) -> tuple[list[type[Node]], int]:
        comb_node: Node = self._node(node)
        assert isinstance(comb_node, CombinationNode)
        return comb_node.selections(), comb_node.selection_index()

    def set_selection(self, node: NodeId, index: int) -> None:
        comb_node: Node = self._node(node)
        assert isinstance(comb_node, CombinationNode)
        comb_node.set_selection(index)
