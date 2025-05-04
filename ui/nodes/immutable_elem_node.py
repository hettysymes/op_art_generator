# Import necessary types for pre-registration
import importlib
import pickle
import sys

from ui.id_generator import gen_uid
from ui.nodes.nodes import UnitNode, UnitNodeInfo
from ui.nodes.shape_datatypes import Group, Element
from ui.port_defs import PortDef


# Base class for immutable element nodes
class ImmutableElementNode(UnitNode):
    """Base class for immutable element nodes."""
    UNIT_NODE_INFO = UnitNodeInfo(
        name="Shape Drawing",
        description="Immutable drawing extracted from a previously rendered node."
    )

    def __init__(self, uid, props, internal_state):
        super().__init__(uid, props, internal_state)

    def compute(self):
        return self.get_prop_val('_element')

    def visualise(self):
        element = self.compute()
        port_type = self.get_port_type_name()
        group = Group(debug_info=f"Immutable Element ({port_type})")
        group.add(element)
        return group

    def get_port_type_name(self):
        """Get the name of the port type for this node."""
        # This will be overridden in subclasses
        return "Unknown"


# Registry for element implementations
ELEMENT_IMPLEMENTATIONS = {}


# Function to create and register a class for a specific element type
def register_element_type(element_type):
    """Register a class for a specific element type."""
    type_name = element_type.__name__

    # Skip if already registered
    if type_name in ELEMENT_IMPLEMENTATIONS:
        return ELEMENT_IMPLEMENTATIONS[type_name]

    # Create a class name
    class_name = f"ImmutableElementNode_{type_name}"

    # Create a class directly
    class ElementNodeClass(ImmutableElementNode):
        # Define the node info with proper port type
        UNIT_NODE_INFO = UnitNodeInfo(
            name="Shape Drawing",
            out_port_defs=[PortDef("Drawing", element_type)],
            description=f"Immutable drawing extracted from a previously rendered node."
        )

        def get_port_type_name(self):
            return type_name

    # Set the class name for better debugging and pickle compatibility
    ElementNodeClass.__name__ = class_name
    ElementNodeClass.__qualname__ = class_name

    # Register the class in the module's global namespace for pickle
    module = sys.modules[__name__]
    setattr(module, class_name, ElementNodeClass)

    # Register in our local registry
    ELEMENT_IMPLEMENTATIONS[type_name] = ElementNodeClass
    return ElementNodeClass


# Function to create a node from an element
def get_node_from_element(element: Element):
    # Get the element type
    element_type = element.get_output_type()
    type_name = element_type.__name__

    # Register the type if needed
    if type_name not in ELEMENT_IMPLEMENTATIONS:
        register_element_type(element_type)

    # Get the implementation class
    ElementClass = ELEMENT_IMPLEMENTATIONS[type_name]

    # Create an instance
    return ElementClass(
        gen_uid(),
        {},
        {'_element': element}
    )


# Pre-register common element types (do this at module import time)
def pre_register_common_types():
    """Pre-register common element types to ensure they're available for pickle."""
    try:
        # Try to import common element types
        from your_library import PT_Polyline, Rectangle, Circle, Path  # Adjust imports as needed
        common_types = [PT_Polyline, Rectangle, Circle, Path]

        # Register each type
        for element_type in common_types:
            register_element_type(element_type)
    except ImportError:
        # If types can't be imported, we'll register them on-demand
        pass


# Call pre-registration at module import time
pre_register_common_types()


# For pickle compatibility: custom unpickler that dynamically registers missing classes
class ElementNodeUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        # First try the normal approach
        try:
            return super().find_class(module, name)
        except AttributeError:
            # If the class is not found and it looks like one of our element nodes
            if name.startswith('ImmutableElementNode_'):
                # Extract the type name
                type_name = name.split('_', 1)[1]

                # Try to find and register the type
                try:
                    # This assumes your element types can be imported from somewhere
                    type_module_name = 'ui.port_defs'
                    type_module = importlib.import_module(type_module_name)
                    element_type = getattr(type_module, type_name)

                    # Register the type
                    register_element_type(element_type)

                    # Try again to get the class
                    return super().find_class(module, name)
                except (ImportError, AttributeError):
                    raise AttributeError(f"Can't find class {name} in module {module}")

            # If it's not one of our element nodes or we can't register it, raise the original error
            raise AttributeError(f"Can't find class {name} in module {module}")


# Helper function to load a scene with custom unpickler
def load_scene_with_elements(filepath):
    """Load a scene with custom unpickler for element nodes."""
    with open(filepath, 'rb') as f:
        unpickler = ElementNodeUnpickler(f)
        return unpickler.load()