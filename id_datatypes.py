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
type PropKey = str


@dataclass(frozen=True)
class PortId:
    node: NodeId
    key: PropKey
    is_input: bool


def output_port(node: NodeId, key: PropKey) -> PortId:
    return PortId(node, key, False)


def input_port(node: NodeId, key: PropKey) -> PortId:
    return PortId(node, key, True)


def node_changed_port(node: NodeId, port: PortId) -> PortId:
    return PortId(node, port.key, port.is_input)


# Edge ID
@dataclass(frozen=True)
class EdgeId:
    src_port: PortId
    dst_port: PortId

    @property
    def src_node(self) -> NodeId:
        return self.src_port.node

    @property
    def dst_node(self) -> NodeId:
        return self.dst_port.node

    @property
    def src_key(self) -> PropKey:
        return self.src_port.key

    @property
    def dst_key(self) -> PropKey:
        return self.dst_port.key
