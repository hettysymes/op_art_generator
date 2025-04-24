from enum import Enum, auto


class PortType(Enum):
    FUNCTION = auto()
    WARP = auto()
    GRID = auto()
    ELEMENT = auto()
    VALUE_LIST = auto()
    GRADIENT = auto()
    VISUALISABLE = auto()


class PortDef:

    def __init__(self, name, port_type, input_multiple=False):
        self.name = name
        self.port_type = port_type
        self.input_multiple = input_multiple


visualisable_types = [PortType.GRID, PortType.ELEMENT]

def is_port_type_compatible(src_type, dst_type):
    if dst_type == PortType.VISUALISABLE:
        return src_type in visualisable_types
    return src_type == dst_type
