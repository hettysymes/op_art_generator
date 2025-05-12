from collections import defaultdict, deque

from ui.id_generator import gen_uid, shorten_uid
from ui.nodes.node_defs import GraphQuerier, PortRef
from ui.nodes.port_defs import PortType, PortIO


class NodeGraph(GraphQuerier):
    def __init__(self):
        self.edges = set()  # edges are ((src_node, src_port), (dst_node, dst_port))
        self.node_map = {}
        self.node_inputs = defaultdict(set)  # dst_node → set of src_nodes
        self.node_outputs = defaultdict(set)  # src_node → set of dst_nodes

        self.port_refs = {} # Map (dst_node_id, dst_port_key) to [ref map, next id]
        self.inactive_port_ids = {}

    def clear_compute_results(self):
        for node in self.node_map.values():
            node.clear_compute_results()
        return self

    def add_new_node(self, node_class, add_info=None, node_id=None):
        uid = node_id or gen_uid()
        self.node_map[uid] = node_class(uid, self, add_info=add_info)
        return uid

    def add_existing_node(self, node):
        self.node_map[node.uid] = node

    def remove_node(self, node_id):
        # Assumes related node connections have been removed
        del self.node_map[node_id]

    def node(self, node_id):
        return self.node_map[node_id]

    def output_node_ids(self, node_id):
        return self.node_outputs.get(node_id, set())

    def add_edge(self, src_conn_id, dst_conn_id):
        src_node_id, src_port_key = src_conn_id
        dst_node_id, dst_port_key = dst_conn_id
        self.edges.add((src_conn_id, dst_conn_id))
        self.node_outputs[src_node_id].add(dst_node_id)
        self.node_inputs[dst_node_id].add(src_node_id)

    def remove_edge(self, src_conn_id, dst_conn_id):
        src_node_id, src_port_key = src_conn_id
        dst_node_id, dst_port_key = dst_conn_id
        self.edges.discard((src_conn_id, dst_conn_id))
        # Check if any other edges exist from src to dst
        still_connected = any(
            s == src_node_id and d == dst_node_id
            for (s, _), (d, _) in self.edges
        )
        if not still_connected:
            self.node_outputs[src_node_id].discard(dst_node_id)
            self.node_inputs[dst_node_id].discard(src_node_id)
        # Remove port ref if it exists
        if dst_conn_id in self.port_refs:
            id_to_port_refs = self.port_refs[dst_conn_id]['ref_map']
            for ref_id, conn_id in id_to_port_refs.items():
                if conn_id == src_conn_id:
                    del id_to_port_refs[ref_id]
                    break

    def get_port_refs_for_port(self, node_id, port_key):
        return self.port_refs.get((node_id, port_key))

    def extend_port_refs(self, new_port_refs):
        self.port_refs.update(new_port_refs)

    def _input_sources(self, node_id, port_key):
        """Return a set of (src_node_id, src_port_key) that are connected to the given input port."""
        return {
            src_port_id
            for src_port_id, (dst_node_id, dst_port_key) in self.edges
            if dst_node_id == node_id and dst_port_key == port_key
        }

    def get_port_ref(self, node_id, port_key, ref_id):
        src_node_id, src_port_key = self.port_refs[(node_id, port_key)]['ref_map'][ref_id]
        src_base_node_name = self.node(src_node_id).base_node_name()
        src_port_def = self.node(src_node_id).get_port_defs()[(PortIO.OUTPUT, src_port_key)]
        return PortRef(src_node_id, src_port_key, src_base_node_name, src_port_def)

    def active_input_ports(self, node_id):
        """Return a set of input port keys on the given node that have something connected."""
        # Only return port keys where the input is not None
        active_ports = set()
        for ((src_node_id, src_port_key), (dst_node_id, dst_port_key)) in self.edges:
            if dst_node_id != node_id: continue
            if self.node(src_node_id).get_compute_result(src_port_key) is not None:
                active_ports.add(dst_port_key)
        return active_ports

    def active_output_ports(self, node_id):
        """Return a set of output port keys on the given node that have something connected."""
        return {
            src_port_key
            for ((src_node_id, src_port_key), _) in self.edges
            if src_node_id == node_id
        }

    def port_input(self, node_id, port_key, get_refs=False):
        # Get node input at specified port, returns a list as multiple nodes may be connected
        found_src_port_ids = self._input_sources(node_id, port_key)
        if not found_src_port_ids:
            raise KeyError("Input node not found for given port.")
        # Return node computes
        result = []
        id_to_port_refs = None
        port_refs_to_id = None
        # Set up for references if needed
        if get_refs:
            if (node_id, port_key) not in self.port_refs:
                self.port_refs[(node_id, port_key)] = {'ref_map': {}, 'next_id': 1} # Create entry
            id_to_port_refs = self.port_refs[(node_id, port_key)]['ref_map']
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
                    ref_id = self.port_refs[(node_id, port_key)]['next_id']
                    # Update internal state
                    self.port_refs[(node_id, port_key)]['next_id'] += 1
                    id_to_port_refs[ref_id] = src_port_id
                # Add compute result
                result.append((ref_id, compute_result))
            else:
                # Simply add the compute result
                result.append(compute_result)
        return result

    def mark_inactive_port_id(self, node_id, port_id):
        self.inactive_port_ids.setdefault(node_id, []).append(port_id)

    def pop_inactive_port_ids(self, node_id):
        return self.inactive_port_ids.pop(node_id, [])

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