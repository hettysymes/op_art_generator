class AppState:

    def __init__(self, view_pos, zoom, node_states, node_graph, custom_node_defs):
        self.view_pos = view_pos
        self.zoom = zoom
        self.node_states = node_states
        self.node_graph = node_graph
        self.custom_node_defs = custom_node_defs # maps name to custom node def

class CustomNodeDef:
    def __init__(self, subgraph, selected_ports, vis_node_id, description=None):
        self.subgraph = subgraph
        self.selected_ports = selected_ports # Maps node_id to list of port_ids
        self.vis_node_id = vis_node_id
        self.description = description

class NodeState:

    def __init__(self, node_id, ports_open, pos, svg_size):
        self.node_id = node_id
        self.ports_open = ports_open
        self.pos = pos
        self.svg_size = svg_size