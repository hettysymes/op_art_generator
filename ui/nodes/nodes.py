from abc import ABC, abstractmethod

from ui.nodes.drawers.blank_canvas_drawer import BlankCanvas


class PropTypeList:

    def __init__(self, prop_types):
        self.prop_types = prop_types

    def get_default_values(self):
        prop_vals = {}
        for prop_type in self.prop_types:
            prop_vals[prop_type.name] = prop_type.default_value
        return prop_vals

    def __iter__(self):
        return iter(self.prop_types)


class PropType:
    """Defines a property for a node"""

    def __init__(self, name, prop_type, default_value=None, min_value=None, max_value=None,
                 options=None, description=""):
        self.name = name
        self.prop_type = prop_type  # "int", "float", "string", "bool", "enum"
        self.default_value = default_value
        self.min_value = min_value
        self.max_value = max_value
        self.options = options  # For enum type
        self.description = description


class Node(ABC):

    def __init__(self, node_id, input_nodes, prop_vals):
        self.node_id = node_id
        self.input_nodes = input_nodes
        self.prop_vals = prop_vals
        self.init_attributes()  # To override
        self.prop_vals = prop_vals if prop_vals else self.prop_type_list.get_default_values()

    def init_attributes(self):
        self.name = "Node"
        self.resizable = True
        self.in_port_defs = []
        self.out_port_defs = []
        self.prop_type_list = PropTypeList([])

    def get_svg_path(self, height, wh_ratio):
        vis = self.visualise(height, wh_ratio)
        if vis: return vis
        # No visualisation, return blank canvas
        return BlankCanvas(f"tmp/{str(self.node_id)}", height, wh_ratio).save()

    @abstractmethod
    def compute(self):
        pass

    @abstractmethod
    def visualise(self, height, wh_ratio):
        pass


class UnitNode(Node):

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def compute(self):
        return

    def visualise(self, height, wh_ratio):
        return


class CombinationNode(Node):

    def __init__(self, node_id, input_nodes, prop_vals, selection_index):
        self.unit_node = None
        self.selections = None
        self.selection_index = selection_index
        self.init_selections()
        super().__init__(node_id, input_nodes, prop_vals)

    def init_selections(self):
        self.selections = []

    def init_attributes(self):
        self.init_selections()
        self.set_selection(self.selection_index, at_init=True)

    def set_selection(self, index, at_init=False):
        self.selection_index = index
        prop_vals = self.prop_vals if at_init else None
        self.unit_node = self.selections[index](self.node_id, self.input_nodes, prop_vals)
        self.name = self.unit_node.name
        self.resizable = self.unit_node.resizable
        self.in_port_defs = self.unit_node.in_port_defs
        self.out_port_defs = self.unit_node.out_port_defs
        self.prop_type_list = self.unit_node.prop_type_list
        if not at_init:
            for k in self.prop_vals:
                if k in self.unit_node.prop_vals:
                    self.unit_node.prop_vals[k] = self.prop_vals[k]
            self.prop_vals = self.unit_node.prop_vals

    def compute(self):
        self.unit_node.input_nodes = self.input_nodes
        self.unit_node.prop_vals = self.prop_vals
        return self.unit_node.compute()

    def visualise(self, height, wh_ratio):
        self.unit_node.input_nodes = self.input_nodes
        self.unit_node.prop_vals = self.prop_vals
        return self.unit_node.visualise(height, wh_ratio)
