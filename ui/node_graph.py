from ui.id_generator import gen_uid, shorten_uid
from ui.nodes.node_defs import GraphQuerier, PortRef
from ui.nodes.port_defs import PortType, PortIO


class NodeGraph(GraphQuerier):
    def __init__(self, nodes=None, connections=None):
        self.nodes = nodes if nodes else {} # Map node id to node
        self.connections = connections if connections else []
        self.port_refs = {} # Map (dst_node_id, dst_port_key) to [ref map, next id]

    def add_new_node(self, node_class, add_info=None, node_id=None):
        uid = node_id if node_id else gen_uid()
        self.nodes[uid] = node_class(uid, self, add_info=add_info)
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
        # Remove port ref if it exists
        if dst_conn_id in self.port_refs:
            id_to_port_refs = self.port_refs[dst_conn_id]['ref_map']
            id_to_delete = None
            for ref_id, conn_id in id_to_port_refs.items():
                if conn_id == src_conn_id:
                    id_to_delete = ref_id
                    break
            if id_to_delete:
                del id_to_port_refs[id_to_delete]

    def get_port_ref(self, node_id, port_key, ref_id):
        src_node_id, src_port_key = self.port_refs[(node_id, port_key)]['ref_map'][ref_id]
        src_port_display_name = self.node(src_node_id).get_port_defs()[(PortIO.OUTPUT, src_port_key)].display_name
        return PortRef(src_node_id, src_port_key, src_port_display_name)

    def active_input_ports(self, node_id):
        return [
                    dst_port_key
                    for (_, (dst_node, dst_port_key)) in self.connections
                    if dst_node == node_id
                ]

    def port_input(self, node_id, port_key, get_refs=False):
        # Get node input at specified port, returns a list as multiple nodes may be connected
        found_src_port_ids = [
            src_port_id
            for src_port_id, (dst_node_id, dst_port_key) in self.connections
            if dst_node_id == node_id and dst_port_key == port_key
        ]
        if not found_src_port_ids:
            raise KeyError("Input node not found for given port.")
        # Return node computes
        if get_refs:
            result = []
            if (node_id, port_key) not in self.port_refs:
                self.port_refs[(node_id, port_key)] = {'ref_map': {}, 'next_id': 0} # Create entry
            id_to_port_refs = self.port_refs[(node_id, port_key)]['ref_map']
            port_refs_to_id = {port_ref: ref_id for ref_id, port_ref in id_to_port_refs.items()}
            for src_port_id in found_src_port_ids:
                # Get ref id
                if src_port_id in port_refs_to_id:
                    ref_id = port_refs_to_id[src_port_id]
                else:
                    ref_id = self.port_refs[(node_id, port_key)]['next_id']
                    # Update internal state
                    self.port_refs[(node_id, port_key)]['next_id'] += 1
                    id_to_port_refs[ref_id] = src_port_id
                # Add compute to result
                src_node_id, src_port_key = src_port_id
                result.append((ref_id, self.nodes[src_node_id].compute(src_port_key)))
        else:
            result = [self.nodes[src_node_id].compute(src_port_key) for src_node_id, src_port_key in found_src_port_ids]
        return result

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