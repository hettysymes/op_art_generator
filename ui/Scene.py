class Scene:

    def __init__(self):
        self.nodes = []

class NodeState:

    def __init__(self, pos, input_ports, output_ports, property_values, node_type):
        self.pos = pos
        self.input_ports = input_ports
        self.output_ports = output_ports
        self.property_values = property_values
        self.node_type = node_type

class EdgeState:

    def __init__(self, src_port, dst_port):
        self.src_port = src_port
        self.dst_port = dst_port

class PortState:

    def __init__(self, node, is_input, edges, port_type):
        self.node = node
        self.is_input = is_input
        self.edges = edges
        self.port_type = port_type