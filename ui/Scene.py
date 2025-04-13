from ui.nodes import Node

class Scene:

    def __init__(self):
        self.states = {}

    def add(self, elem):
        self.states[elem.uid] = elem

    def get(self, uid):
        return self.states[uid]

    def remove(self, uid):
        del self.states[uid]

class NodeState:

    def __init__(self, uid, x, y, input_port_ids, output_port_ids, property_values, node_class: Node, svg_width, svg_height):
        self.uid = uid
        self.x = x
        self.y = y
        self.input_port_ids = input_port_ids
        self.output_port_ids = output_port_ids
        self.property_values = property_values
        self.node_class = node_class
        self.svg_width = svg_width
        self.svg_height = svg_height

class EdgeState:

    def __init__(self, uid, src_port_id, dst_port_id):
        self.uid = uid
        self.src_port_id = src_port_id
        self.dst_port_id = dst_port_id

class PortState:

    def __init__(self, uid, x, y, parent_node_id, is_input, edge_ids, port_type):
        self.uid = uid
        self.x = x
        self.y = y
        self.parent_node_id = parent_node_id
        self.is_input = is_input
        self.edge_ids = edge_ids
        self.port_type = port_type