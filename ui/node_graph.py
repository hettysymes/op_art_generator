from ui.id_generator import gen_uid, shorten_uid
from ui.nodes.node_defs import GraphQuerier
from ui.nodes.port_defs import PortType, PortIO


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

    def remove_node(self, node_id):
        # Assumes related node connections have been removed
        del self.nodes[node_id]

    def node(self, node_id):
        return self.nodes[node_id]

    def output_node_ids(self, node_id):
        output_node_ids = []
        for (src_node_id, src_port_key), (dst_node_id, dst_port_key) in self.connections:
            if src_node_id == node_id:
                output_node_ids.append(dst_node_id)
        return output_node_ids

    def add_connection(self, src_conn_id, dst_conn_id):
        self.connections.append((src_conn_id, dst_conn_id))

    def remove_connection(self, src_conn_id, dst_conn_id):
        self.connections.remove((src_conn_id, dst_conn_id))

    def active_input_ports(self, node_id):
        return [
                    dst_port_key
                    for (_, (dst_node, dst_port_key)) in self.connections
                    if dst_node == node_id
                ]

    def port_input(self, node_id, port_key):
        # Get node input
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

    def __str__(self):
        result = ""
        for (src_node_id, src_port_key), (dst_node_id, dst_port_key) in self.connections:
            src_node_name = self.node(src_node_id).name()
            dst_node_name = self.node(dst_node_id).name()
            src_port_display_name = self.node(src_node_id).get_port_defs()[(PortIO.OUTPUT, src_port_key)].display_name
            dst_port_display_name = self.node(dst_node_id).get_port_defs()[(PortIO.INPUT, dst_port_key)].display_name
            first_string = f"{src_node_name} [#{shorten_uid(src_node_id)}] (port \"{src_port_display_name}\")".ljust(40)
            second_string = f"{dst_node_name} [#{shorten_uid(dst_node_id)}] (port \"{dst_port_display_name}\")"
            result += f"{first_string} -> {second_string}\n"
        if not result:
            result = "[no connections]\n"
        return result