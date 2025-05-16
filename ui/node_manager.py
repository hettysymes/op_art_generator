import copy
from dataclasses import dataclass
from typing import Optional

from fontTools.subset.svg import subset_elements

from ui.id_datatypes import NodeId, PortId, PropKey, input_port, output_port, gen_node_id
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

    def _node_impl(self, node: NodeId):
        return self.node_map[node]

    def add_node(self, node: NodeId, node_impl):
        self.node_map[node] = node_impl

    def remove_node(self, node: NodeId):
        self.node_map.pop(node, None)

    def resolve_property(self, src_port: PortId, inp_type: PropType) -> Optional[PropValue]:
        src_node_impl = self._node_impl(src_port.node)
        comp_result: Optional[PropValue] = src_node_impl.get_compute_result(src_port.key)
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
        node_impl = self._node_impl(node)
        return NodeInfo(
            uid=node,
            name=node_impl.name(),
            base_name=node_impl.base_name,
            description=node_impl.description,
            prop_defs=node_impl.prop_defs,
            randomisable=node_impl.randomisable,
            selectable=isinstance(node_impl, SelectableNode),
            combination=isinstance(node_impl, CombinationNode)
        )

    def get_property(self, node: NodeId, key: PropKey) -> Optional[PropValue]:
        return self._node_impl(node).prop_vals.get(key)

    def set_property(self, node: NodeId, key: PropKey, value: PropValue) -> None:
        self._node_impl(node).prop_vals[key] = value

    def visualise(self, node: NodeId) -> Visualisable:
        return self._node_impl(node).visualise()

    def selections_w_idx(self, node: NodeId) -> tuple[list[type[Node]], int]:
        comb_node: Node = self._node_impl(node)
        assert isinstance(comb_node, CombinationNode)
        return comb_node.selections(), comb_node.selection_index()

    def set_selection(self, node: NodeId, index: int) -> None:
        comb_node: Node = self._node_impl(node)
        assert isinstance(comb_node, CombinationNode)
        comb_node.set_selection(index)

    def new_node_manager(self, subset: Optional[set[NodeId]] = None, new_ids: bool = False) -> "NodeManager" | tuple["NodeManager", dict[NodeId, NodeId]]:
        new_node_manager = NodeManager()
        old_to_new_id_map: dict[NodeId, NodeId] = {}
        nodes_to_copy: set[NodeId] = subset if subset is not None else self.node_map.keys()
        for node in nodes_to_copy:
            node_impl = copy.deepcopy(self._node_impl(node))
            if new_ids:
                node_id: NodeId = gen_node_id()
                node_impl.uid = node_id
                old_to_new_id_map[node] = node_id
            else:
                node_id: NodeId = node
            new_node_manager.add_node(node_id, node_impl)
        if new_ids:
            return new_node_manager, old_to_new_id_map
        else:
            return new_node_manager

    def update_nodes(self, other_node_manager: "NodeManager") -> None:
        self.node_map.update(other_node_manager.node_map)


