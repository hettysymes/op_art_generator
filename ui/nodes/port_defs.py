from enum import Enum, auto


class PortType:
    pass


# Function

class PT_Function(PortType):
    pass


# Warp

class PT_Warp(PortType):
    pass


# Grid
class PT_Grid(PortType):
    pass


# Elements
class PT_Repeatable(PortType):
    pass


class PT_Element(PT_Repeatable):
    pass


class PT_Shape(PT_Element):
    pass


class PT_Ellipse(PT_Shape):
    pass


class PT_Polyline(PT_Element):
    pass


# Value Lists

class PT_ValueList(PortType):
    pass


class PT_ColourList(PT_ValueList):
    pass


class PT_NumberList(PT_ValueList):
    pass


class PT_PointList(PT_ValueList):
    pass


# Element List

class PT_ElementList(PT_Repeatable):
    pass


# Fill
class PT_Fill(PortType):
    pass


class PT_Gradient(PT_Fill):
    pass


class PT_Colour(PT_Fill):
    pass

class PortIO(Enum):
    INPUT = auto()
    OUTPUT = auto()

def filter_port_ids(port_ids, port_io):
    return [port_key for (io, port_key) in port_ids if io == port_io]

class PortDef:

    def __init__(self, display_name, port_type, optional=False):
        self.display_name = display_name
        self.port_type = port_type,
        self.optional = optional
