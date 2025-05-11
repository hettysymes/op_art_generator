from abc import ABC, abstractmethod
from enum import Enum, auto


class PortType(ABC):

    @abstractmethod
    def is_compatible_with(self, dest_type):
        pass

# List
class PT_List(PortType):
    def __init__(self, item_type: PortType):
        self.item_type = item_type

    def is_compatible_with(self, dest_type) -> bool:
        if isinstance(dest_type, PT_List):
            # List-to-list: inner types must be compatible
            return self.item_type.is_compatible_with(dest_type.item_type)
        return False

# Scalar
class PT_Scalar(PortType):
    def is_compatible_with(self, dest_type):
        if isinstance(dest_type, PT_List):
            # Scalar-to-list: inner types must be compatible
            return self.is_compatible_with(dest_type.item_type)
        return isinstance(self, type(dest_type))

# Function

class PT_Function(PT_Scalar):
    pass


# Warp

class PT_Warp(PT_Scalar):
    pass


# Grid
class PT_Grid(PT_Scalar):
    pass


# Elements

class PT_Element(PT_Scalar):
    def __init__(self, element_type=None):
        if element_type is None:
            self.element_type = PT_Group()
        elif not isinstance(element_type, PT_Group):
            raise TypeError("element_type must be an instance of PT_Group or its subclass")
        else:
            self.element_type = element_type

    def is_compatible_with(self, dest_type):
        if isinstance(dest_type, PT_List):
            return self.is_compatible_with(dest_type.item_type)
        if isinstance(dest_type, PT_Element):
            return isinstance(self.element_type, type(dest_type.element_type))
        return False

class PT_Group(PT_Scalar):
    pass

class PT_Shape(PT_Group):
    pass

class PT_Polyline(PT_Shape):
    pass

class PT_Polygon(PT_Shape):
    pass

class PT_Ellipse(PT_Shape):
    pass

# Sampling

class PT_Point(PT_Scalar):
    pass

# Fill

class PT_Fill(PT_Scalar):
    pass


class PT_Gradient(PT_Fill):
    pass


class PT_Colour(PT_Fill):
    pass

class PortRefTableEntry:
    def __init__(self, ref_id, deletable, port_data, own_data=None):
        self.ref_id = ref_id
        self.deletable = deletable
        self.port_data = port_data
        self.own_data = own_data

# Tables

class LineRef(PortRefTableEntry):
    def __init__(self, ref_id, deletable, port_data, own_data=False):
        super().__init__(ref_id, deletable, port_data, own_data)
    def points(self):
        return self.port_data
    def reversed(self):
        return self.own_data
    def toggle_reverse(self):
        self.own_data = not self.reversed()
    def points_w_reversal(self):
        return list(reversed(self.points())) if self.reversed() else self.points()

class PT_PortRefTable(PT_Scalar):
    def __init__(self, linked_port_key=None):
        self.linked_port_key = linked_port_key

class PT_ElemRefTable(PT_PortRefTable):
    pass

class PT_PointRefTable(PT_PortRefTable):
    pass

# Other

class PT_Number(PT_Scalar):
    def __init__(self, min_value=None, max_value=None):
        self.min_value = min_value if min_value else -999999
        self.max_value = max_value if max_value else 999999

class PT_Float(PT_Number):
    def __init__(self, min_value=None, max_value=None, decimals=3):
        super().__init__(min_value, max_value)
        self.decimals = decimals

class PT_Int(PT_Number):
    pass

class PT_Bool(PT_Scalar):
    pass

class PT_PropEnum(PT_Scalar):
    pass

class PT_SelectorEnum(PT_Scalar):
    pass

class PT_Enum(PT_Scalar):
    def __init__(self, options=None, display_options=None):
        self.options = None
        self.display_options = None
        self.set_options(options, display_options)

    def set_options(self, options=None, display_options=None):
        if options:
            self.options = options
            if display_options:
                assert len(display_options) == len(options)
            self.display_options = display_options if display_options else options
        else:
            self.options = [None]
            self.display_options = ["[none]"]

    def get_options(self):
        return self.options

    def display_data_options(self):
        return zip(self.display_options, self.options)

class PT_ColourTable(PT_Scalar):
    pass

class PT_Hidden(PT_Scalar):
    pass

class PT_String(PT_Scalar):
    pass


class PropEntry:
    """Defines a property for a node"""

    def __init__(self, prop_type, display_name=None, description=None, default_value=None, auto_format=True):
        self.prop_type = prop_type  # "int", "float", "string", "bool", "enum"
        self.display_name = display_name
        self.description = description
        self.default_value = default_value
        self.auto_format = auto_format


class PortIO(Enum):
    INPUT = auto()
    OUTPUT = auto()


class PortDef:

    def __init__(self, display_name, port_type, optional=False, description=None):
        self.display_name = display_name
        self.port_type = port_type
        self.optional = optional
        self.description = description
