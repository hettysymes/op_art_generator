import copy
import os
import traceback
from abc import ABC, abstractmethod

from ui.id_generator import shorten_uid
from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.drawers.error_drawer import ErrorDrawer
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.shape_datatypes import Group, Element


class PropTypeList:

    def __init__(self, prop_types):
        self.prop_types = prop_types

    def get_default_values(self):
        prop_vals = {}
        for prop_type in self.prop_types:
            prop_vals[prop_type.key_name] = copy.deepcopy(prop_type.default_value)
        return prop_vals

    def get_port_modifiable_keynames(self):
        key_names = []
        for prop_type in self.prop_types:
            if prop_type.port_modifiable:
                key_names.append(prop_type.key_name)
        return key_names

    def __iter__(self):
        return iter(self.prop_types)


class PropType:
    """Defines a property for a node"""

    def __init__(self, key_name, prop_type, default_value=None, min_value=None, max_value=None,
                 description="", display_name=None, auto_format=True, options=None, port_modifiable=False):
        self.key_name = key_name
        self.display_name = display_name if display_name else key_name
        self.prop_type = prop_type  # "int", "float", "string", "bool", "enum"
        self.default_value = default_value
        self.min_value = min_value
        self.max_value = max_value
        self.description = description
        self.auto_format = auto_format
        self.options = options  # options for (constant) enum type
        self.port_modifiable = port_modifiable


class UnitNodeInfo:

    def __init__(self, name, resizable, selectable, in_port_defs, out_port_defs, prop_type_list, description,
                 prop_port_defs=None):
        self.name = name
        self.resizable = resizable
        self.selectable = selectable
        self.in_port_defs = in_port_defs
        self.out_port_defs = out_port_defs
        self.prop_type_list = prop_type_list
        self.description = description
        self.prop_port_defs = prop_port_defs if (prop_port_defs is not None) else []


class Node(ABC):

    def __init__(self, node_id, input_nodes, prop_vals):
        self.node_id = node_id
        self.input_nodes = input_nodes if input_nodes else {}
        self.prop_vals = prop_vals if prop_vals else self.node_info().prop_type_list.get_default_values()

    def _return_path(self, temp_dir):
        return os.path.join(temp_dir, self.node_id)

    def safe_visualise(self):
        exception = None
        # Catch exception if raised
        # try:
        #     vis = self.visualise()
        # except NodeInputException as e:
        #     exception = e
        #     if e.node_id == self.node_id:
        #         msg = str(e.message)
        #     else:
        #         msg = f"Error further up pipeline (id #{shorten_uid(e.node_id)})."
        #     vis = ErrorDrawer(self._return_path(temp_dir), height, wh_ratio, [e.title, msg]).save()
        # except Exception as e:
        #     exception = e
        #     vis = ErrorDrawer(self._return_path(temp_dir), height, wh_ratio, ["Unknown Exception", str(e)]).save()
        #     traceback.print_exc()
        # # Return visualisation with exception
        # if not vis:
        #     # No visualisation, return blank canvas
        #     vis = ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (Group(), None)).save()
        # return vis, exception
        return self.visualise()

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

    def prop_port_defs(self):
        return self.node_info().prop_port_defs

    def _is_multiple_input(self, key_name):
        for port_def in self.in_port_defs():
            if port_def.key_name == key_name:
                return port_def.input_multiple
        assert False

    def _is_port_modifiable(self, key_name):
        return key_name in self.prop_type_list().get_port_modifiable_keynames()

    def get_input_node(self, key_name):
        if self._is_multiple_input(key_name):
            default = []
            if key_name in self.input_nodes:
                res = self.input_nodes[key_name]
                return res if (res is not None) else default
            return default
        else:
            default = UnitNode()
            if key_name in self.input_nodes:
                res = self.input_nodes[key_name]
                return res[0] if (res is not None) else default
            return default

    def get_prop_val(self, key_name):
        default = self.prop_vals[key_name]
        if self._is_port_modifiable(key_name) and key_name in self.input_nodes:
            res = self.input_nodes[key_name]
            if res is not None:
                res_compute = res[0].compute()
                if res_compute is not None:
                    return res_compute
        return default

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
    def visualise(self):
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

    def __init__(self, node_id=None, input_nodes=None, prop_vals=None):
        super().__init__(node_id, input_nodes, prop_vals)

    @classmethod
    def node_info(cls):
        return cls.UNIT_NODE_INFO

    @classmethod
    def display_name(cls):
        return cls.node_info().name

    def compute(self):
        return

    def visualise(self):
        return self.compute()


class CombinationNode(Node):
    NAME = "Combination Node"
    SELECTIONS = []

    def __init__(self, node_id=None, input_nodes=None, prop_vals=None, selection_index=None):
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

    def visualise(self):
        return self.node_instance().visualise()
