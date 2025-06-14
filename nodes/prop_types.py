class PropType:

    def __init__(self, input_multiple=False):
        self.input_multiple = input_multiple

    def is_compatible_with(self, dest_type):
        return True

    def __repr__(self):
        return self.__class__.__name__


def find_closest_common_base(types):
    # Convert instances to types if needed
    types = [t if isinstance(t, type) else type(t) for t in types]

    # Get MROs for all types
    mro_lists = [t.mro() for t in types]

    # Iterate through the MRO of the first type
    for cls in mro_lists[0]:
        # Check if this cls is in the MROs of all other types
        if all(cls in mro for mro in mro_lists[1:]):
            return cls  # Found the closest common base

    return object  # Fallback if no common base


# Scalar
class PT_Scalar(PropType):

    def is_compatible_with(self, dest_type):
        if isinstance(dest_type, PT_ValProbPairHolder):
            return True
        if isinstance(dest_type, PT_List):
            # Scalar-to-list: inner types must be compatible
            return self.is_compatible_with(dest_type.base_item_type)
        return isinstance(self, type(dest_type))


# List
class PT_List(PropType):
    def __init__(self, base_item_type: PT_Scalar = PT_Scalar(), input_multiple: bool = False,
                 depth: int = 1, extract=True):
        self.base_item_type = base_item_type
        self.depth = depth
        self.extract = extract
        super().__init__(input_multiple)

    def is_compatible_with(self, dest_type):
        if isinstance(dest_type, PT_ValProbPairHolder):
            return True
        if not isinstance(self, type(dest_type)):
            return False
        if isinstance(dest_type, PT_List):
            return self.base_item_type.is_compatible_with(dest_type.base_item_type)
        return True  # Connected to PropType()

    def __repr__(self):
        return f"List({repr(self.base_item_type)}, depth={self.depth})"


# Function

class PT_Function(PT_Scalar):
    pass


# Warp

class PT_Warp(PT_Scalar):
    pass


# Grid
class PT_Grid(PT_Scalar):
    pass


# Sampling

class PT_PointsHolder(PT_Scalar):
    pass


class PT_Point(PT_PointsHolder):
    pass


# Elements

class PT_ElementHolder(PT_Scalar):
    pass


class PT_Element(PT_ElementHolder):
    pass


class PT_Shape(PT_Element):
    pass


class PT_Polyline(PT_Shape, PT_PointsHolder):
    pass


class PT_Polygon(PT_Shape):
    pass


class PT_Ellipse(PT_Shape):
    pass


# Fill

class PT_FillHolder(PT_Scalar):
    pass


class PT_Fill(PT_FillHolder):
    pass


class PT_Gradient(PT_Fill):
    pass


class PT_Colour(PT_Fill):
    pass


class PT_GradOffset(PT_Scalar):
    pass


class PT_ValProbPairHolder(PT_Scalar):
    pass


# Other

class PT_Number(PT_Scalar):
    def __init__(self, min_value=None, max_value=None):
        super().__init__()
        self.min_value = min_value if min_value is not None else -999999
        self.max_value = max_value if max_value is not None else 999999

    def is_compatible_with(self, dest_type):
        if isinstance(dest_type, PT_ValProbPairHolder):
            return True
        if isinstance(dest_type, PT_List):
            # Scalar-to-list: inner types must be compatible
            return self.is_compatible_with(dest_type.base_item_type)
        if isinstance(dest_type, PT_Number):
            # Check the min-max range within the dest type min-max range
            return dest_type.min_value <= self.min_value and dest_type.max_value >= self.max_value
        return isinstance(self, type(dest_type))


class PT_Int(PT_Number):
    pass


class PT_Bool(PT_Scalar):
    pass


class PT_Enum(PT_Scalar):
    pass


class PT_String(PT_Scalar):
    pass


class PT_BlazeCircleDef(PT_Scalar):
    pass
