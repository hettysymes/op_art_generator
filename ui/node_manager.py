from typing import Optional

from ui.id_datatypes import NodeId, PortId, PropKey
from ui.nodes.node_defs import Node
from ui.nodes.prop_defs import PropValue, PropType


class NodeManager:

    def __init__(self):
        self.node_map: dict[NodeId, Node] = {}

    def resolve_property(self, src_port: PortId, inp_type: PropType) -> Optional[PropValue]:
        src_node: Node = self.node_map[src_port.node]
        comp_result: Optional[PropValue] = src_node.get_compute_result(src_port.key)
        if not comp_result:
            return None
        # Check types of the result, assume they are already compatible

        return None
