from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, TypeVar, cast


def get_most_general_type(types):  # Look for a type that all others are compatible with
    for candidate in types:
        if all(other.is_compatible_with(candidate) for other in types):
            return candidate

    return PropType()  # Default to most general type


class PropType:

    def is_compatible_with(self, dest_type):
        return True

    def __repr__(self):
        return self.__class__.__name__

# Scalar
class PT_Scalar(PropType):

    def is_compatible_with(self, dest_type):
        if isinstance(dest_type, PT_List):
            # Scalar-to-list: inner types must be compatible
            return self.is_compatible_with(dest_type.scalar_type)
        return isinstance(self, type(dest_type))

# List
class PT_List(PropType):
    def __init__(self, scalar_type: PT_Scalar = PT_Scalar(), input_multiple: bool = False, depth: int = 1):
        self.scalar_type = scalar_type
        self.input_multiple = input_multiple
        self.depth = depth

    def is_compatible_with(self, dest_type):
        if not isinstance(self, type(dest_type)):
            return False
        if isinstance(dest_type, PT_List):
           return self.scalar_type.is_compatible_with(dest_type.scalar_type)
        return True # Connected to PropType()

    def __repr__(self):
        return f"List({repr(self.scalar_type)}, depth={self.depth})"



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


class PT_ColourRefTable(PT_PortRefTable):
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


class PT_Hidden(PT_Scalar):
    pass


class PT_String(PT_Scalar):
    pass

class PortStatus(Enum):
    COMPULSORY = auto()
    OPTIONAL = auto()
    FORBIDDEN = auto()

class PropValue(ABC):

    @property
    @abstractmethod
    def type(self) -> PropType:
        pass

@dataclass(frozen=True)
class PropDef:
    input_port_status: PortStatus = PortStatus.OPTIONAL
    output_port_status: PortStatus = PortStatus.OPTIONAL
    prop_type: PropType = PropType()
    display_name: str = ""
    description: str = ""
    default_value: Optional[PropValue] = None
    auto_format: bool = True

# PROP VALUES

class List(PropValue):
    def __init__(self, item_type: PropType, items: list[PropValue]):
        self.item_type = item_type
        self.items = items

    @property
    def type(self) -> PropType:
        if isinstance(self.item_type, PT_List):
            return PT_List(
                scalar_type=self.item_type.scalar_type,
                depth=self.item_type.depth + 1
            )
        elif isinstance(self.item_type, PT_Scalar):
            return PT_List(scalar_type=self.item_type, depth=1)
        else:
            raise TypeError(f"Invalid item_type: {type(self.item_type)}")

    def extract(self, extract_type: PropType) -> PropValue:
        """
        Normalize `self` to match the shape of `extract_type`.
        Flatten then re-nest to match the scalar type and depth.
        """
        # Determine target depth (0 = scalar)
        target_depth = extract_type.depth if isinstance(extract_type, PT_List) else 0

        # Step 1: Fully flatten the value
        flat: List = flatten(self)

        # Step 2: Validate scalar type compatibility
        target_scalar_type = (
            extract_type.scalar_type
            if isinstance(extract_type, PT_List)
            else extract_type
        )

        # Step 3: Return scalar if depth is 0
        if target_depth == 0:
            assert len(flat.items) == 1, f"Expected single scalar value, got {len(flat.items)}"
            scalar = flat.items[0]
            assert isinstance(scalar.type, PT_Scalar)
            return scalar

        # Step 4: Re-nest to match target depth
        nested = flat
        for _ in range(target_depth - 1):
            nested = List(item_type=nested.type, items=[nested])

        # Final outer List uses scalar_type and depth to compute correct item_type
        return List(item_type=nested.type, items=nested.items)

    def append(self, item: PropValue) -> None:
        if not item.type.is_compatible_with(self.item_type):
            raise TypeError(f"Invalid type: expected {self.item_type}, got {item.type}")
        self.items.append(item)

    def __iter__(self):
        return iter(self.items)

    def __getitem__(self, index: int) -> PropValue:
        return self.items[index]

    def __len__(self) -> int:
        return len(self.items)

    def __repr__(self):
        return f"List({repr(self.item_type)}, items={self.items})"


def flatten(x: PropValue) -> List:
    if isinstance(x, List):
        flat_items = []
        for item in x.items:
            flat_items.extend(flatten(item).items)
        item_type = x.item_type.scalar_type if isinstance(x.item_type, PT_List) else x.item_type
        return List(item_type=item_type, items=flat_items)
    else:
        assert isinstance(x.type, PT_Scalar)
        return List(item_type=x.type, items=[x])


class Colour(PropValue):

    def __init__(self, red: float = 0, green: float = 0, blue: float = 0, alpha: float = 255):
        self.rgba = (red, green, blue, alpha)

    @property
    def type(self) -> PropType:
        return PT_Colour()

class Int(int, PropValue):
    def __new__(cls, value: int):
        return super().__new__(cls, value)

    def __init__(self, value: int):
        self.value = value

    @property
    def type(self) -> PropType:
        return PT_Int()