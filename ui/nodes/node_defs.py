import copy
import traceback
from abc import ABC, abstractmethod
from enum import Enum, auto

from ui.id_generator import shorten_uid
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.shape_datatypes import Group
from ui.vis_types import ErrorFig

class GraphQuerier(ABC):

    @abstractmethod
    def active_input_ports(self, node_id): # Return input port keys connected to a node
        pass

    @abstractmethod
    def input_node(self, node_id, port_key):
        pass

class PropTypeList:

    def __init__(self, prop_types):
        self.prop_types = prop_types

    def default_values(self):
        prop_vals = {}
        for prop_type in self.prop_types:
            prop_vals[prop_type.key_name] = copy.deepcopy(prop_type.default_value)
        return prop_vals

    def is_empty(self):
        for prop in self.prop_types:
            if prop.prop_type != "hidden":
                return False
        return True

    def __iter__(self):
        return iter(self.prop_types)

class PropType(Enum):
    POINT_TABLE = auto()
    FILL = auto()
    FLOAT = auto()


class PropEntry:
    """Defines a property for a node"""

    def __init__(self, prop_type, display_name=None, description=None, default_value=None, min_value=None, max_value=None,
                 auto_format=True, options=None):

        self.prop_type = prop_type  # "int", "float", "string", "bool", "enum"
        self.display_name = display_name
        self.description = description
        self.default_value = default_value
        self.min_value = min_value
        self.max_value = max_value
        self.auto_format = auto_format
        self.options = options  # options for (constant) enum type

class NodeInfo:

    def __init__(self, description, port_defs=None, prop_type_list=None):
        self.description = description
        self.port_defs = port_defs if port_defs else {}
        self.prop_type_list = prop_type_list if prop_type_list else PropTypeList([])

class BaseNode:

    def compute(self):
        return

class Node(BaseNode, ABC):
    NAME = None

    def __init__(self, uid, graph_querier, prop_vals):
        self.uid = uid
        self.graph_querier = graph_querier
        self.prop_vals = prop_vals if prop_vals else self.prop_type_list().default_values()

    def safe_visualise(self):
        # Catch exception if raised
        try:
            vis = self.visualise()
        except NodeInputException as e:
            if e.node_id == self.uid:
                msg = str(e.message)
            else:
                msg = f"Error further up pipeline (id #{shorten_uid(e.node_id)})."
            vis = ErrorFig(e.title, msg)
        except Exception as e:
            vis = ErrorFig("Unknown Exception", str(e))
            traceback.print_exc()
        if not vis:
            # No visualisation, return blank canvas
            vis = Group(debug_info="Blank Canvas")
        return vis

    # Getter functions for node info
    def description(self):
        return self.node_info().description

    def port_defs(self):
        return self.node_info().port_defs

    def prop_type_list(self):
        return self.node_info().prop_type_list

    # Private functions
    def _active_input_ports(self):
        return self.graph_querier.active_input_ports(self.uid)

    def _input_node(self, port_key):
        input_node = self.graph_querier.input_node(self.uid, port_key)
        return input_node if input_node else BaseNode()

    def _prop_val(self, prop_key):
        if prop_key in self._active_input_ports():
            prop_node_val = self._input_node(prop_key).compute()
            if prop_node_val:
                return prop_node_val
        return self.prop_vals[prop_key]

    @classmethod
    def name(cls):
        return cls.NAME

    # Functions to implement
    @abstractmethod
    def base_node_name(self):
        pass

    @abstractmethod
    def node_info(self):
        pass

    @abstractmethod
    def compute(self):
        pass

    @abstractmethod
    def visualise(self):
        pass
