from enum import Enum, auto

class PortType(Enum):
    FUNCTION = auto()
    WARP = auto()
    GRID = auto()
    ELEMENT = auto()
    VISUALISABLE = auto()

visualisable_types = [PortType.GRID, PortType.ELEMENT]

def is_port_type_compatible(src_type, dst_type):
    if dst_type == PortType.VISUALISABLE:
        return src_type in visualisable_types
    return src_type == dst_type
