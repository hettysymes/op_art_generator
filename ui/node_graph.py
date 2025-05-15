from collections import defaultdict, deque
from dataclasses import dataclass, field
from itertools import count
from typing import Optional, ItemsView

from ui.app_state import NodeId
from ui.id_datatypes import gen_node_id, EdgeId, PortId, PropKey
from ui.nodes.node_defs import GraphQuerier, PortRef, Node
from ui.nodes.port_defs import PortIO

type RefId = int
class RefPorts:

    def __init__(self):
        self._id_counter = count(1)
        self.map: dict[RefId, PortId] = {}

    def add(self, port: PortId) -> RefId:
        ref_id = next(self._id_counter)
        self.map[ref_id] = port
        return ref_id

class NodeGraph(GraphQuerier):
    def __init__(self):
        self.edges: set[EdgeId] = set()
        self.node_map: dict[NodeId, Node] = {}
        self.node_inputs: defaultdict[NodeId, set[NodeId]] = defaultdict(set)  # dst_node → set of src_nodes
        self.node_outputs: defaultdict[NodeId, set[NodeId]] = defaultdict(set)  # src_node → set of dst_nodes

        self.ref_ports: dict[PortId, RefPorts] = defaultdict(RefPorts) # map destination port to its port ref
        self.inactive_ports: defaultdict[NodeId, set[PortId]] = defaultdict(set)

    def clear_compute_results(self):
        for node in self.node_map.values():
            node.clear_compute_results()
        return self

    def add_new_node(self, node_class, add_info=None, node_id: Optional[NodeId] =None):
        uid: NodeId = node_id or gen_node_id()
        self.node_map[uid] = node_class(uid, self, add_info=add_info)
        return uid

    def add_existing_node(self, node_impl: Node):
        self.node_map[node_impl.uid] = node_impl

    def remove_node(self, node: NodeId):
        # Assumes related node connections have been removed
        del self.node_map[node]

    def node(self, node: NodeId) -> Node:
        return self.node_map[node]

    def output_nodes(self, node: NodeId):
        return self.node_outputs.get(node, set())

    def add_edge(self, edge: EdgeId):
        self.edges.add(edge)
        self.node_outputs[edge.src_node].add(edge.dst_node)
        self.node_inputs[edge.dst_node].add(edge.src_node)

    def remove_edge(self, edge: EdgeId):
        self.edges.discard(edge)
        # Check if any other edges exist from src node to dst node to update topology
        still_connected = any(
            e.src_node == edge.src_node and e.dst_node == edge.dst_node
            for e in self.edges
        )
        if not still_connected:
            self.node_outputs[edge.src_node].discard(edge.dst_node)
            self.node_inputs[edge.dst_node].discard(edge.src_node)
        # Remove port ref if it exists
        if edge.dst_port in self.ref_ports:
            ref_port: RefPorts = self.ref_ports[edge.dst_port]
            ref_port.map = {ref: port for ref, port in ref_port.map.items() if port != edge.src_port}

    def get_ref_port(self, port: PortId) -> Optional[RefPorts]:
        return self.ref_ports.get(port)

    def extend_ref_ports(self, new_ref_ports) -> None:
        self.ref_ports.update(new_ref_ports)

    def conn_src_ports(self, dst_port: PortId) -> set[PortId]:
        """Return a set of (output) ports that are connected to the given input port."""
        return {
            edge.src_port
            for edge in self.edges
            if edge.dst_port == dst_port
        }

    def active_input_port_keys(self, node: NodeId) -> set[PropKey]:
        """Return a set of input ports on the given node that have something connected."""
        # Only return port keys where the input is not None
        return {
            edge.dst_key
            for edge in self.edges
            if edge.dst_node == node and self.node(edge.src_node).get_compute_result(edge.src_key) is not None
        }

    def active_output_port_keys(self, node: NodeId) -> set[PropKey]:
        """Return a set of output port keys on the given node that have something connected."""
        return {
            edge.src_key
            for edge in self.edges
            if edge.src_node == node
        }

    def unconnected_ports(self, node_id):
        """Return a set of port ids on the given node that don't have something connected."""
        unconnected_ports = set(self.node(node_id).get_port_defs().keys())
        for (src_node_id, src_port_key), (dst_node_id, dst_port_key) in self.edges:
            if src_node_id == node_id:
                unconnected_ports.discard((PortIO.OUTPUT, src_port_key))
            elif dst_node_id == node_id:
                unconnected_ports.discard((PortIO.INPUT, dst_port_key))
        return unconnected_ports

    def edges_to_node(self, node_id):
        return [edge for edge in self.edges if edge[1][0] == node_id]

    def port_input(self, node_id, port_key, get_refs=False):
        # Get node input at specified port, returns a list as multiple nodes may be connected
        found_src_port_ids = self.conn_src_ports(node_id, port_key)
        if not found_src_port_ids:
            raise KeyError("Input node not found for given port.")
        # Return node computes
        result = []
        id_to_port_refs = None
        port_refs_to_id = None
        # Set up for references if needed
        if get_refs:
            if (node_id, port_key) not in self.ref_ports:
                self.ref_ports[(node_id, port_key)] = {'ref_map': {}, 'next_id': 1} # Create entry
            id_to_port_refs = self.ref_ports[(node_id, port_key)]['ref_map']
            port_refs_to_id = {port_ref: ref_id for ref_id, port_ref in id_to_port_refs.items()}
        for src_port_id in found_src_port_ids:
            # Check if compute result is None, otherwise skip
            src_node_id, src_port_key = src_port_id
            compute_result = self.node(src_node_id).get_compute_result(src_port_key)
            if compute_result is None: continue
            # The compute result is not None
            if get_refs:
                # Get ref id
                if src_port_id in port_refs_to_id:
                    ref_id = port_refs_to_id[src_port_id]
                else:
                    ref_id = self.ref_ports[(node_id, port_key)]['next_id']
                    # Update internal state
                    self.ref_ports[(node_id, port_key)]['next_id'] += 1
                    id_to_port_refs[ref_id] = src_port_id
                # Add compute result
                result.append((ref_id, compute_result))
            else:
                # Simply add the compute result
                result.append(compute_result)
        return result

    def mark_inactive_port_id(self, node_id, port_id):
        self.inactive_ports.setdefault(node_id, []).append(port_id)

    def pop_inactive_port_ids(self, node_id):
        return self.inactive_ports.pop(node_id, [])

    def get_topo_order_subgraph(self, subset=None):
        subset = set(subset) if subset is not None else set(self.node_map.keys())

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