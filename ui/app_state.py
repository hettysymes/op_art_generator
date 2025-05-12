class AppState:

    def __init__(self, view_pos, zoom, node_states, node_graph, custom_node_defs):
        self.view_pos = view_pos
        self.zoom = zoom
        self.node_states = node_states
        self.node_graph = node_graph
        self.custom_node_defs = custom_node_defs # maps name to custom node def

class CustomNodeDef:
    def __init__(self, subgraph, inp_node_id, out_node_id, ports_open):
        self.subgraph = subgraph
        self.inp_node_id = inp_node_id
        self.out_node_id = out_node_id
        self.ports_open = ports_open

class NodeState:

    def __init__(self, node_id, ports_open, pos, svg_size):
        self.node_id = node_id
        self.ports_open = ports_open
        self.pos = pos
        self.svg_size = svg_size