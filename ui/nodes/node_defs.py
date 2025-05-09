import copy
import traceback
from abc import ABC, abstractmethod
from enum import Enum, auto

from ui.id_generator import shorten_uid
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.port_defs import PortIO
from ui.nodes.shape_datatypes import Group
from ui.vis_types import ErrorFig

class GraphQuerier(ABC):

    @abstractmethod
    def active_input_ports(self, node_id): # Return input port keys connected to a node
        pass

    @abstractmethod
    def port_input(self, node_id, port_key):
        pass

class PropType(Enum):
    POINT_TABLE = auto()
    FILL = auto()
    FLOAT = auto()
    INT = auto()
    BOOL = auto()
    COORDINATE = auto()
    PROP_ENUM = auto()
    SELECTOR_ENUM = auto()
    ENUM = auto()
    ELEM_TABLE = auto()
    COLOUR_TABLE = auto()
    HIDDEN = auto()


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

    def __init__(self, description, port_defs=None, prop_entries=None):
        self.description = description
        self.port_defs = port_defs if port_defs else {}
        self.prop_entries = prop_entries if prop_entries else {}

class BaseNode:

    def compute(self):
        return

class Node(BaseNode, ABC):
    NAME = None # To override

    def __init__(self, uid, graph_querier, prop_vals=None):
        self.uid = uid
        self.graph_querier = graph_querier
        self.prop_vals = prop_vals if prop_vals else self._default_prop_vals()

    def _default_prop_vals(self):
        default_prop_vals = {}
        for prop_key, prop_entry in self.get_prop_entries().items():
            default_prop_vals[prop_key] = prop_entry.default_value
        return default_prop_vals

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
    def get_description(self):
        return self.get_node_info().description

    def get_port_defs(self):
        return self.get_node_info().port_defs

    def port_defs_filter_by_io(self, port_io):
        return {port_key: port_def for (io, port_key), port_def in self.get_port_defs().items() if io == port_io}

    def get_prop_entries(self):
        return self.get_node_info().prop_entries

    def set_property(self, prop_key, value):
        self.prop_vals[prop_key] = value

    def get_property(self, prop_key):
        return self.prop_vals[prop_key]

    def prop_entries_is_empty(self):
        for prop_entry in self.get_prop_entries().values():
            if prop_entry.prop_type != PropType.HIDDEN:
                return False
        return True

    def compulsory_ports(self):
        compulsory_ports = []
        for port_id, port_def in self.get_port_defs().items():
            if not port_def.optional:
                compulsory_ports.append(port_id)
        return compulsory_ports

    # Private functions
    def _active_input_ports(self):
        return self.graph_querier.active_input_ports(self.uid)

    def _port_input(self, port_key):
        return self.graph_querier.port_input(self.uid, port_key)

    def _prop_val(self, prop_key):
        if prop_key in self._active_input_ports():
            prop_node_val = self._port_input(prop_key)
            if prop_node_val:
                return prop_node_val
        return self.prop_vals.get(prop_key)

    @classmethod
    def name(cls):
        return cls.NAME

    # Functions to implement
    @abstractmethod
    def base_node_name(self):
        pass

    @abstractmethod
    def get_node_info(self):
        pass

    @abstractmethod
    def compute(self, out_port_key='_main'):
        pass

    @abstractmethod
    def visualise(self):
        pass
