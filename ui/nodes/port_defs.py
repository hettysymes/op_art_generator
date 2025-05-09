from abc import ABC, abstractclassmethod, abstractmethod
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
    pass


class PT_Shape(PT_Element):
    pass


class PT_Ellipse(PT_Shape):
    pass


class PT_Polyline(PT_Element):
    pass


# Sampling

class PT_Float(PT_Scalar):
    pass


class PT_Point(PT_Scalar):
    pass

# Fill

class PT_Fill(PT_Scalar):
    pass


class PT_Gradient(PT_Fill):
    pass


class PT_Colour(PT_Fill):
    pass


class PortIO(Enum):
    INPUT = auto()
    OUTPUT = auto()


class PortDef:

    def __init__(self, display_name, port_type, optional=False, description=None):
        self.display_name = display_name
        self.port_type = port_type
        self.optional = optional
        self.description = description
