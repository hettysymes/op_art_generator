
import uuid
from dataclasses import dataclass

# Node ID
@dataclass(frozen=True)
class NodeId:
    value: str

    def __str__(self):
        return f"#{self.value[:3]}"

def gen_node_id() -> NodeId:
    return NodeId(str(uuid.uuid4()))

# Port ID
type PortKey = str
@dataclass(frozen=True)
class PortId:
    node_id: NodeId
    port_key: PortKey
    is_input: bool

# Edge ID
@dataclass(frozen=True)
class EdgeId:
    src_port_id: PortId
    dst_port_id: PortId