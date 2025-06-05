import copy
from dataclasses import dataclass
from typing import Optional

from sympy import Number

from id_datatypes import NodeId, PortId, PropKey, input_port, output_port
from node_graph import NodeGraph
from nodes.node_defs import Node, RuntimeNode, ResolvedProps, ResolvedRefs, RefQuerier, PropDef, PortStatus, \
    NodeCategory, DisplayStatus
from nodes.node_implementations.canvas import CanvasNode
from nodes.nodes import CombinationNode, SelectableNode
from nodes.prop_types import PropType, PT_List, PT_Int
from nodes.prop_values import PropValue, List, Float
from nodes.shape_datatypes import Group
from vis_types import Visualisable


@dataclass(frozen=True)
class NodeInfo:
    uid: NodeId
    name: str
    category: NodeCategory
    base_name: str
    description: str
    prop_defs: dict[PropKey, PropDef]
    randomisable: bool
    selectable: bool
    combination: bool
    animatable: bool
    is_canvas: bool

    def filter_ports_by_status(self, port_status: PortStatus, get_input=True, get_output=True) -> list[PortId]:
        results = []
        for key, prop_def in self.prop_defs.items():
            if get_input and prop_def.input_port_status == port_status:
                results.append(input_port(node=self.uid, key=key))
            if get_output and prop_def.output_port_status == port_status:
                results.append(output_port(node=self.uid, key=key))
        return results

    def requires_property_box(self) -> bool:
        return any(
            prop_def.display_status != DisplayStatus.NO_DISPLAY
            for prop_def in self.prop_defs.values()
        )

class NodeManager:

    def __init__(self):
        self.node_map: dict[NodeId, RuntimeNode] = {}
        self.node_graph: NodeGraph = NodeGraph()

    def _runtime_node(self, node: NodeId) -> RuntimeNode:
        return self.node_map[node]

    def add_node(self, node: NodeId, base_node: Node, compute_results=None):
        self.node_map[node] = RuntimeNode(uid=node, graph_querier=self.node_graph, node_querier=self, node=base_node,
                                          compute_results=compute_results)

    def get_compute_inputs(self, node: NodeId) -> tuple[ResolvedProps, ResolvedRefs, RefQuerier]:
        return self._runtime_node(node).get_compute_inputs()

    def get_compute_results(self, node: NodeId) -> dict[PropKey, PropValue]:
        return self._runtime_node(node).compute_results

    def remove_node(self, node: NodeId):
        self.node_map.pop(node, None)

    def resolve_property(self, src_port: PortId, inp_type: PropType) -> Optional[PropValue]:
        src_runtime_node = self._runtime_node(src_port.node)
        comp_result: Optional[PropValue] = src_runtime_node.get_compute_result(src_port.key)
        if comp_result is None:
            return None
        # Check types of the result, assume they are already compatible
        if isinstance(inp_type, PT_List):
            if isinstance(comp_result, List) and inp_type.extract:
                return comp_result.extract(inp_type)
            else:
                return List(comp_result.type, [comp_result])
        elif isinstance(inp_type, PT_Int) and isinstance(comp_result, Float):
            return comp_result.to_int()
        # Input type is either PropType or Scalar, return value as is
        return comp_result

    def node_info(self, node: NodeId) -> NodeInfo:
        runtime_node = self._runtime_node(node)
        return NodeInfo(
            uid=node,
            name=runtime_node.node.name(),
            category=runtime_node.node.node_category(),
            base_name=runtime_node.node.base_name,
            description=runtime_node.node.description,
            prop_defs=runtime_node.node.prop_defs,
            randomisable=runtime_node.node.randomisable,
            selectable=isinstance(runtime_node.node, SelectableNode),
            combination=isinstance(runtime_node.node, CombinationNode),
            animatable=runtime_node.node.animatable,
            is_canvas=isinstance(runtime_node.node, CanvasNode)
        )

    def get_compute_result(self, node: NodeId, key: PropKey) -> Optional[PropValue]:
        runtime_node: RuntimeNode = self._runtime_node(node)
        return runtime_node.get_compute_result(key)

    def get_internal_property(self, node: NodeId, key: PropKey) -> Optional[PropValue]:
        return self._runtime_node(node).node.internal_props.get(key)

    def set_internal_property(self, node: NodeId, key: PropKey, value: PropValue) -> None:
        self._runtime_node(node).node.internal_props[key] = value

    def visualise(self, node: NodeId) -> Visualisable:
        return self._runtime_node(node).visualise()

    def compute(self, node: NodeId) -> None:
        self._runtime_node(node).compute()

    def selections_w_idx(self, node: NodeId) -> tuple[list[type[Node]], int]:
        comb_node: Node = self._runtime_node(node).node
        assert isinstance(comb_node, CombinationNode)
        return comb_node.selections(), comb_node.selection_index()

    def set_selection(self, node: NodeId, index: int) -> None:
        comb_node: Node = self._runtime_node(node).node
        assert isinstance(comb_node, CombinationNode)
        comb_node.set_selection(index)

    def get_node_copies(self, subset: Optional[set[NodeId]] = None) -> dict[NodeId, Node]:
        nodes_to_copy: set[NodeId] = subset if subset is not None else self.node_map.keys()
        return {
            node: copy.deepcopy(self.node_map[node].node)
            for node in nodes_to_copy
        }

    def update_nodes(self, base_nodes: dict[NodeId, Node]) -> None:
        for node, base_node in base_nodes.items():
            self.node_map[node] = RuntimeNode(uid=node, graph_querier=self.node_graph, node_querier=self,
                                              node=base_node)

    def randomise(self, node: NodeId, seed=None) -> None:
        random_node: Node = self._runtime_node(node).node
        random_node.randomise(seed=seed)

    def get_seed(self, node: NodeId, seed=None) -> float:
        random_node: Node = self._runtime_node(node).node
        return random_node.get_seed()

    def extract_element(self, node: NodeId, parent_group: Group, element_id: str) -> PropKey:
        runtime_node: RuntimeNode = self._runtime_node(node)
        assert isinstance(runtime_node.node, SelectableNode)
        return runtime_node.extract_element(parent_group, element_id)

    def is_playing(self, node: NodeId) -> bool:
        animate_node: Node = self._runtime_node(node).node
        assert animate_node.animatable
        return animate_node.playing

    def playing_nodes(self) -> set[NodeId]:
        return {
            node for node, runtime_node in self.node_map.items()
            if runtime_node.node.animatable and runtime_node.node.playing
        }

    def reanimate(self, node: NodeId, time: float) -> bool:
        animate_node: Node = self._runtime_node(node).node
        assert animate_node.animatable
        return animate_node.reanimate(time)

    def toggle_play(self, node: NodeId) -> None:
        animate_node: Node = self._runtime_node(node).node
        assert animate_node.animatable
        animate_node.toggle_play()
