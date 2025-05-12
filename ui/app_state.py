class AppState:

    def __init__(self, view_pos, zoom, node_states, node_graph):
        self.view_pos = view_pos
        self.zoom = zoom
        self.node_states = node_states
        self.node_graph = node_graph

class NodeState:

    def __init__(self, node_id, ports_open, pos, svg_size):
        self.node_id = node_id
        self.ports_open = ports_open
        self.pos = pos
        self.svg_size = svg_size