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

class PT_Element(PortType):
    pass

class PT_Polyline(PT_Element):
    pass

class PT_Ellipse(PT_Element):
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

class PT_ElementList(PortType):
    pass

# Gradient

class PT_Gradient(PortType):
    pass


class PortDef:

    def __init__(self, name, port_type, input_multiple=False):
        self.name = name
        self.port_type = port_type
        self.input_multiple = input_multiple
