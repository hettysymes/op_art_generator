from ui.id_generator import gen_uid
from ui.nodes.node_defs import GraphQuerier


class NodeGraph(GraphQuerier):
    def __init__(self, nodes=None, connections=None):
        self.nodes = nodes if nodes else {} # Map node id to node
        self.connections = connections if connections else []

    def add_new_node(self, node_class):
        uid = gen_uid()
        self.nodes[uid] = node_class(uid, self)
        return uid

    def add_existing_node(self, node):
        self.nodes[node.uid] = node

    def node(self, node_id):
        return self.nodes[node_id]

    def add_connection(self, src_node_id, src_port_key, dst_node_id, dst_port_key):
        self.connections.append(((src_node_id, src_port_key), (dst_node_id, dst_port_key)))

    def active_input_ports(self, node_id):
        return [
                    dst_port_key
                    for (_, (dst_node, dst_port_key)) in self.connections
                    if dst_node == node_id
                ]

    def port_input(self, node_id, port_key):
        # Find input node
        found_src_port_id = None
        for src_port_id, (dst_node_id, dst_port_key) in self.connections:
            if dst_node_id == node_id and dst_port_key == port_key:
                found_src_port_id = src_port_id
                break
        if not found_src_port_id:
            raise KeyError("Input node not found for given port.")
        # Return node compute
        src_node_id, src_port_key = found_src_port_id
        return self.nodes[src_node_id].compute(src_port_key)
