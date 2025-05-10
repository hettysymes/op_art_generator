class PortRefTableEntry:
    def __init__(self, ref_id, deletable, port_data, own_data=None):
        self.ref_id = ref_id
        self.deletable = deletable
        self.port_data = port_data
        self.own_data = own_data

class PropType:
    pass

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

class PrT_PortRefTable(PropType):
    def __init__(self, linked_port_key=None):
        self.linked_port_key = linked_port_key

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

class PrT_Point(PropType):
    pass

class PrT_PropEnum(PropType):
    pass

class PrT_SelectorEnum(PropType):
    pass

class PrT_Enum(PropType):
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

class PrT_ColourTable(PropType):
    pass

class PrT_Hidden(PropType):
    pass

class PrT_String(PropType):
    pass


class PropEntry:
    """Defines a property for a node"""

    def __init__(self, prop_type, display_name=None, description=None, default_value=None, min_value=None,
                 max_value=None, auto_format=True):
        self.prop_type = prop_type  # "int", "float", "string", "bool", "enum"
        self.display_name = display_name
        self.description = description
        self.default_value = default_value
        self.min_value = min_value
        self.max_value = max_value
        self.auto_format = auto_format