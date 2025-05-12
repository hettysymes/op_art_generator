import traceback
from abc import ABC, abstractmethod

from ui.id_generator import shorten_uid
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.port_defs import PortIO, PT_Scalar, PT_Hidden, PT_List
from ui.nodes.shape_datatypes import Group
from ui.vis_types import ErrorFig


class PortRef:
    def __init__(self, node_id, port_key, base_node_name, port_def):
        self.node_id = node_id
        self.port_key = port_key
        self.base_node_name = base_node_name
        self.port_def = port_def


class GraphQuerier(ABC):

    @abstractmethod
    def node(self, node_id):
        pass

    @abstractmethod
    def get_port_ref(self, node_id, port_key, ref_id):
        pass

    @abstractmethod
    def active_input_ports(self, node_id):  # Return input port keys connected to a node
        pass

    @abstractmethod
    def active_output_ports(self, node_id):  # Return output port keys connected to a node
        pass

    @abstractmethod
    def port_input(self, node_id, port_key, get_refs=False):
        pass

    @abstractmethod
    def mark_inactive_port_id(self, node_id, port_id):
        pass


class NodeInfo:

    def __init__(self, description, port_defs=None, prop_entries=None):
        self.description = description
        self.port_defs = port_defs if port_defs else {}
        self.prop_entries = prop_entries if prop_entries else {}


class Node(ABC):
    NAME = None  # To override

    def __init__(self, uid, graph_querier, prop_vals=None):
        self.uid = uid
        self.graph_querier = graph_querier
        self.prop_vals = prop_vals if prop_vals else self._default_prop_vals()
        self.compute_results = {}

    def _default_prop_vals(self):
        default_prop_vals = {}
        for prop_key, prop_entry in self.get_prop_entries().items():
            default_prop_vals[prop_key] = prop_entry.default_value
        return default_prop_vals

    def safe_visualise(self):
        # Catch exception if raised
        try:
            # Recompute results
            self.clear_compute_results()
            self.final_compute()
            # Obtain visualisation
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

    def clear_compute_results(self):
        self.compute_results.clear()
        return self

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
            if not isinstance(prop_entry.prop_type, PT_Hidden):
                return False
        return True

    def compulsory_ports(self):
        compulsory_ports = []
        for port_id, port_def in self.get_port_defs().items():
            if not port_def.optional:
                compulsory_ports.append(port_id)
        return compulsory_ports

    def get_compute_result(self, port_key='_main'):
        return self.compute_results.get(port_key)

    def set_compute_result(self, value, port_key='_main'):
        self.compute_results[port_key] = value

    # Private functions
    def _active_input_ports(self):
        return self.graph_querier.active_input_ports(self.uid)

    def _active_output_ports(self):
        return self.graph_querier.active_output_ports(self.uid)

    def _port_input(self, port_key, get_refs=False):
        return self.graph_querier.port_input(self.uid, port_key, get_refs)

    def _prop_val(self, prop_key, get_refs=False):
        if prop_key in self._active_input_ports():
            # Property given by port
            prop_node_vals = self._port_input(prop_key, get_refs)
            # Get port type
            port_type = self.port_defs_filter_by_io(PortIO.INPUT)[prop_key].port_type
            if isinstance(port_type, PT_Scalar):
                return prop_node_vals[0]
            else:
                assert isinstance(port_type, PT_List)
                if not port_type.input_multiple:
                    return prop_node_vals[0]
                return dict(prop_node_vals) if get_refs else prop_node_vals
        # No overriding from port, default to stored property value entry
        return self.prop_vals.get(prop_key)

    def _port_ref(self, port_key, ref_id):
        return self.graph_querier.get_port_ref(self.uid, port_key, ref_id)

    def _mark_inactive_port_id(self, port_id):
        self.graph_querier.mark_inactive_port_id(self.uid, port_id)

    def final_compute(self):
        return self.compute()

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
    def compute(self):
        pass

    @abstractmethod
    def visualise(self):
        pass
