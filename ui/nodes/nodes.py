import copy
import os
from abc import ABC, abstractmethod

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.drawers.error_drawer import ErrorDrawer
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.shape_datatypes import Element


class PropTypeList:

    def __init__(self, prop_types):
        self.prop_types = prop_types

    def get_default_values(self):
        prop_vals = {}
        for prop_type in self.prop_types:
            prop_vals[prop_type.key_name] = copy.deepcopy(prop_type.default_value)
        return prop_vals

    def __iter__(self):
        return iter(self.prop_types)


class PropType:
    """Defines a property for a node"""

    def __init__(self, key_name, prop_type, default_value=None, min_value=None, max_value=None,
                 description="", display_name=None, auto_format=True):
        self.key_name = key_name
        self.display_name = display_name if display_name else key_name
        self.prop_type = prop_type  # "int", "float", "string", "bool", "enum"
        self.default_value = default_value
        self.min_value = min_value
        self.max_value = max_value
        self.description = description
        self.auto_format = auto_format


class UnitNodeInfo:

    def __init__(self, name, resizable, selectable, in_port_defs, out_port_defs, prop_type_list, description):
        self.name = name
        self.resizable = resizable
        self.selectable = selectable
        self.in_port_defs = in_port_defs
        self.out_port_defs = out_port_defs
        self.prop_type_list = prop_type_list
        self.description = description


class Node(ABC):

    def __init__(self, node_id, input_nodes, prop_vals):
        self.node_id = node_id
        self.input_nodes = input_nodes
        self.prop_vals = prop_vals if prop_vals else self.node_info().prop_type_list.get_default_values()

    def _return_path(self, temp_dir):
        return os.path.join(temp_dir, str(self.node_id))

    def get_svg_path(self, temp_dir, height, wh_ratio):
        exception = None
        # Catch exception if raised
        try:
            vis = self.visualise(temp_dir, height, wh_ratio)
        except NodeInputException as e:
            exception = e
            if e.node_id == self.node_id:
                msg = str(e.message)
            else:
                msg = f"Error further up pipeline (id #{e.node_id.hex[:3]})."
            vis = ErrorDrawer(self._return_path(temp_dir), height, wh_ratio, [e.title, msg]).save()
        except Exception as e:
            exception = e
            vis = ErrorDrawer(self._return_path(temp_dir), height, wh_ratio, ["Unknown Exception", str(e)]).save()
        # Return visualisation with exception
        if not vis:
            # No visualisation, return blank canvas
            vis = ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (Element(), None)).save()
        return vis, exception

    def name(self):
        return self.node_info().name

    def resizable(self):
        return self.node_info().resizable

    def selectable(self):
        return self.node_info().selectable

    def in_port_defs(self):
        return self.node_info().in_port_defs

    def out_port_defs(self):
        return self.node_info().out_port_defs

    def prop_type_list(self):
        return self.node_info().prop_type_list

    def description(self):
        return self.node_info().description

    @abstractmethod
    def node_info(self):
        pass

    @classmethod
    @abstractmethod
    def display_name(cls):
        pass

    @abstractmethod
    def compute(self):
        pass

    @abstractmethod
    def visualise(self, temp_dir, height, wh_ratio):
        pass


class UnitNode(Node):
    UNIT_NODE_INFO = UnitNodeInfo(
        name="Unit Node",
        resizable=True,
        selectable=False,
        in_port_defs=[],
        out_port_defs=[],
        prop_type_list=PropTypeList([]),
        description=""
    )

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    @classmethod
    def node_info(cls):
        return cls.UNIT_NODE_INFO

    @classmethod
    def display_name(cls):
        return cls.node_info().name

    def compute(self):
        return

    def visualise(self, temp_dir, height, wh_ratio):
        return


class CombinationNode(Node):
    NAME = "Combination Node"
    SELECTIONS = []

    def __init__(self, node_id, input_nodes, prop_vals, selection_index):
        self.selection_index = selection_index
        super().__init__(node_id, input_nodes, prop_vals)

    @classmethod
    def selections(cls):
        return cls.SELECTIONS

    def node_instance(self):
        return self.selections()[self.selection_index](self.node_id, self.input_nodes, self.prop_vals)

    def node_info(self):
        return self.selections()[self.selection_index].node_info()

    @classmethod
    def display_name(cls):
        return cls.NAME

    def set_selection(self, index):
        self.selection_index = index
        new_prop_vals = self.node_info().prop_type_list.get_default_values()
        # Keep shared properties e.g. fill colour
        for k in self.prop_vals:
            if k in new_prop_vals:
                new_prop_vals[k] = self.prop_vals[k]
        self.prop_vals = new_prop_vals

    def compute(self):
        return self.node_instance().compute()

    def visualise(self, temp_dir, height, wh_ratio):
        return self.node_instance().visualise(temp_dir, height, wh_ratio)
