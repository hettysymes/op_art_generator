import uuid
from collections import defaultdict, deque
from typing import Optional

from ui.app_state import NodeId
from ui.id_datatypes import EdgeId, PortId

# Create a function to generate default RefId values
type RefId = str


def generate_ref_id() -> RefId:
    return str(uuid.uuid4())


# Factory function to create a new port_to_ref dict
def create_port_ref_dict() -> defaultdict[PortId, RefId]:
    return defaultdict(generate_ref_id)


class NodeGraph:
    def __init__(self):
        self.nodes: set[NodeId] = set()
        self.edges: set[EdgeId] = set()
        self.node_inputs: defaultdict[NodeId, set[NodeId]] = defaultdict(set)  # dst_node → set of src_nodes
        self.node_outputs: defaultdict[NodeId, set[NodeId]] = defaultdict(set)  # src_node → set of dst_nodes

        # A node may use information about the source port that is incoming to it (such as node ID, display name)
        # We don't want the node to store this port ID directly as this can change (e.g. the node ID changes after pasting)
        # Hence if we know a node wants information about a port ID, we instead give it a respective ref ID
        # The node can look up information using the ref ID in a safer way, whilst still retaining the relationship with the nodes after pasting
        self.node_to_port_ref: defaultdict[NodeId, defaultdict[PortId, RefId]] = defaultdict(create_port_ref_dict)

    def does_edge_exist(self, edge: EdgeId) -> bool:
        return edge in self.edges

    def add_node(self, node: NodeId) -> None:
        # Add node ID to the nodes set
        self.nodes.add(node)

    def remove_node(self, node: NodeId) -> None:
        # Assumes related node connections have been removed
        self.nodes.discard(node)

    def incoming_edges(self, node_or_port: NodeId | PortId) -> set[EdgeId]:
        # Get edges the with the given node or port as the destination
        if isinstance(node_or_port, NodeId):
            return {
                edge
                for edge in self.edges
                if edge.dst_node == node_or_port
            }
        else:
            return {
                edge
                for edge in self.edges
                if edge.dst_port == node_or_port
            }

    def outgoing_edges(self, node_or_port: NodeId | PortId) -> set[EdgeId]:
        # Get edges the with the given node or port as the source
        if isinstance(node_or_port, NodeId):
            return {
                edge
                for edge in self.edges
                if edge.src_node == node_or_port
            }
        else:
            return {
                edge
                for edge in self.edges
                if edge.src_port == node_or_port
            }

    def get_ref_id(self, node: NodeId, port_to_reference: PortId) -> RefId:
        port_ref_map: defaultdict[PortId, RefId] = self.node_to_port_ref[node]
        return port_ref_map[port_to_reference]

    def extend_port_refs(self, more_node_to_port_refs: dict[NodeId, dict[PortId, RefId]]):
        converted_dict: defaultdict[NodeId, defaultdict[PortId, RefId]] = defaultdict(
            create_port_ref_dict,
            {
                node_id: defaultdict(generate_ref_id, port_dict)
                for node_id, port_dict in more_node_to_port_refs.items()
            }
        )
        self.node_to_port_ref.update(converted_dict)

    def output_nodes(self, node: NodeId) -> set[NodeId]:
        # Get nodes that receive outputs from the given node
        return self.node_outputs.get(node, set())

    def add_edge(self, edge: EdgeId) -> None:
        # Add an edge
        self.edges.add(edge)
        self.node_outputs[edge.src_node].add(edge.dst_node)
        self.node_inputs[edge.dst_node].add(edge.src_node)

    def remove_edge(self, edge: EdgeId) -> None:
        # Remove the edge
        self.edges.discard(edge)
        # Check if any other edges exist from src node to dst node to update topology
        still_connected = any(
            e.src_node == edge.src_node and e.dst_node == edge.dst_node
            for e in self.edges
        )
        if not still_connected:
            self.node_outputs[edge.src_node].discard(edge.dst_node)
            self.node_inputs[edge.dst_node].discard(edge.src_node)
        # Remove the dst node ref mapping to the src port (now unconnected) if it exists
        if edge.dst_node in self.node_to_port_ref:
            port_ref_map: defaultdict[PortId, RefId] = self.node_to_port_ref[edge.dst_node]
            port_ref_map.pop(edge.src_port, None)

    def get_topo_order_subgraph(self, subset: Optional[set[NodeId]] = None) -> list[NodeId]:
        # Given a subset of nodes, get the topological order between them (parent nodes first ending with leaf nodes)
        subset: set[NodeId] = subset if subset is not None else self.nodes

        # Compute in-degrees only for nodes in the subset
        in_degree = {
            n: sum(1 for src in self.node_inputs[n] if src in subset)
            for n in subset
        }

        # Start with nodes in subset that have zero in-degree within the subset
        queue = deque([n for n in subset if in_degree[n] == 0])
        order = []

        while queue:
            node_id = queue.popleft()
            order.append(node_id)
            for neighbor in self.node_outputs[node_id]:
                if neighbor in subset:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        if len(order) != len(subset):
            raise ValueError("Subgraph has cycles or disconnected dependencies.")

        return order