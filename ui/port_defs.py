from enum import Enum, auto


class PortType(Enum):
    FUNCTION = auto()
    WARP = auto()
    GRID = auto()
    ELEMENT = auto()
    VALUE_LIST = auto()
    ITERABLE = auto()
    VISUALISABLE = auto()


class PortDef:

    def __init__(self, name, port_type):
        self.name = name
        self.port_type = port_type


visualisable_types = [PortType.GRID, PortType.ELEMENT]
iterable_types = [PortType.FUNCTION, PortType.VALUE_LIST]

def is_port_type_compatible(src_type, dst_type):
    if dst_type == PortType.VISUALISABLE:
        return src_type in visualisable_types
    elif dst_type == PortType.ITERABLE:
        return src_type in iterable_types
    return src_type == dst_type
