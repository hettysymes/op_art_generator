class PortRefTableEntry:
    def __init__(self, ref_id, deletable, data):
        self.ref_id = ref_id
        self.deletable = deletable
        self.data = data

class PropType:
    pass

# Tables

class PrT_PortRefTable(PropType):
    pass

class PrT_ElemRefTable(PrT_PortRefTable):
    pass

class PrT_PointRefTable(PrT_PortRefTable):
    pass

# Other

class PrT_Fill(PropType):
    pass

class PrT_Float(PropType):
    pass

class PrT_Int(PropType):
    pass

class PrT_Bool(PropType):
    pass

class PrT_Coordinate(PropType):
    pass

class PrT_PropEnum(PropType):
    pass

class PrT_SelectorEnum(PropType):
    pass

class PrT_Enum(PropType):
    pass

class PrT_ColourTable(PropType):
    pass

class PrT_Hidden(PropType):
    pass

class PrT_String(PropType):
    pass


class PropEntry:
    """Defines a property for a node"""

    def __init__(self, prop_type, display_name=None, description=None, default_value=None, min_value=None,
                 max_value=None,
                 auto_format=True, options=None, linked_port_key=None):
        self.prop_type = prop_type  # "int", "float", "string", "bool", "enum"
        self.display_name = display_name
        self.description = description
        self.default_value = default_value
        self.min_value = min_value
        self.max_value = max_value
        self.auto_format = auto_format
        self.options = options  # options for (constant) enum type
        self.linked_port_key = linked_port_key