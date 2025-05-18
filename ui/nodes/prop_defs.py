from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, TypeVar, cast, Generic

from ui.id_datatypes import PropKey
from ui.node_graph import RefId


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

class PT_ListItem(PropType):
    pass

T = TypeVar('T', bound=PropType)
class PT_TableEntry(Generic[T], PT_ListItem):
    def __init__(self, data_type: T):
        self.data_type = data_type

    def is_compatible_with(self, dest_type: PropType) -> bool:
        if isinstance(dest_type, PT_TableEntry):
            return self.data_type.is_compatible_with(dest_type.data_type)
        if isinstance(dest_type, PT_Scalar):
            return self.data_type.is_compatible_with(dest_type)
        return False

# Scalar
class PT_Scalar(PT_ListItem):

    def is_compatible_with(self, dest_type):
        if isinstance(dest_type, PT_List):
            # Scalar-to-list: inner types must be compatible
            return self.is_compatible_with(dest_type.base_item_type)
        elif isinstance(dest_type, PT_TableEntry):
            return self.is_compatible_with(dest_type.data_type)
        return isinstance(self, type(dest_type))

# List
class PT_List(PropType):
    def __init__(self, base_item_type: PT_ListItem = PT_ListItem(), input_multiple: bool = False, depth: int = 1):
        self.base_item_type = base_item_type
        self.input_multiple = input_multiple
        self.depth = depth

    def is_compatible_with(self, dest_type):
        if not isinstance(self, type(dest_type)):
            return False
        if isinstance(dest_type, PT_List):
           return self.base_item_type.is_compatible_with(dest_type.base_item_type)
        return True # Connected to PropType()

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

class PT_Element(PT_Scalar):
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

class PT_Fill(PT_Scalar):
    pass


class PT_Gradient(PT_Fill):
    pass


class PT_Colour(PT_Fill):
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
    display_in_props: bool = True

# PROP VALUES

T = TypeVar('T', bound='PropType')
class List(Generic[T], PropValue):
    def __init__(self, item_type: T, items: Optional[list[PropValue]] = None):
        self.item_type = item_type
        self.items: list[PropValue] = items if items is not None else []

    @property
    def type(self) -> PropType:
        if isinstance(self.item_type, PT_List):
            return PT_List(
                base_item_type=self.item_type.base_item_type,
                depth=self.item_type.depth + 1
            )
        elif isinstance(self.item_type, PT_ListItem):
            return PT_List(base_item_type=self.item_type, depth=1)
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

        # Step 2: Validate base item type compatibility
        target_base_item_type = (
            extract_type.base_item_type
            if isinstance(extract_type, PT_List)
            else extract_type
        )

        # Step 3: Return scalar if depth is 0
        if target_depth == 0:
            assert len(flat.items) == 1, f"Expected single base item value, got {len(flat.items)}"
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

    def reversed(self):
        return List(self.item_type, list(reversed(self.items)))

    def delete(self, idx: int):
        del self.items[idx]

    def extend(self, other_list):
        assert isinstance(other_list, List) and other_list.item_type.is_compatible_with(self.item_type)
        self.items += other_list.items

    def __bool__(self):
        return bool(self.items)

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
        item_type = x.item_type.base_item_type if isinstance(x.item_type, PT_List) else x.item_type
        return List(item_type=item_type, items=flat_items)
    else:
        assert isinstance(x.type, PT_Scalar)
        return List(item_type=x.type, items=[x])


class Colour(tuple, PropValue):
    def __new__(cls, red: float = 0, green: float = 0, blue: float = 0, alpha: float = 255):
        return super().__new__(cls, (red, green, blue, alpha))

    def __init__(self, red: float = 0, green: float = 0, blue: float = 0, alpha: float = 255):
        pass  # No need to store attributes separately; values are in the tuple

    def __reduce__(self):
        return self.__class__, (self[0], self[1], self[2], self[3])

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

class Float(float, PropValue):
    def __new__(cls, value: float):
        return super().__new__(cls, value)

    def __init__(self, value: float):
        self.value = value  # optional, but consistent with your Int class

    @property
    def type(self) -> PropType:
        return PT_Float()

class PointsHolder(PropValue, ABC):
    @property
    @abstractmethod
    def points(self) -> List[PT_Point]:
        pass

    @property
    def type(self) -> PropType:
        return PT_PointsHolder()

class Point(tuple, PointsHolder):

    def __new__(cls, x: float, y: float):
        return super().__new__(cls, (x, y))

    def __init__(self, x: float, y: float):
        # Optional: no need to store self.x/y, values are in the tuple
        pass

    def __reduce__(self):
        return self.__class__, (self[0], self[1])

    @property
    def points(self) -> List[PT_Point]:
        return List(PT_Point(), [self])

    @property
    def type(self) -> PropType:
        return PT_Point()

class Grid(PropValue):
    def __init__(self, v_line_xs: list[float], h_line_ys: list[float]):
        self.v_line_xs = v_line_xs
        self.h_line_ys = h_line_ys

    @property
    def type(self) -> PropType:
        return PT_Grid()

    @property
    def width(self) -> Int:
        return Int(len(self.v_line_xs) - 1)

    @property
    def height(self) -> Int:
        return Int(len(self.h_line_ys) - 1)



class PortRefTableEntry(PropValue):
    def __init__(self, ref: RefId, data: PropValue, deletable: bool = True):
        self.ref = ref
        self.deletable = deletable
        self.data = data

    @property
    def type(self) -> PropType:
        return PT_TableEntry(self.data.type)

# Tables

class LineRef(PointsHolder, PortRefTableEntry):
    def __init__(self, ref: RefId, data: PT_PointsHolder, deletable: bool):
        super().__init__(ref, data, deletable)
        self._reversed = False

    @property
    def points(self) -> List[PT_Point]:
        return cast(PointsHolder, self.data).points

    @property
    def is_reversed(self):
        return self._reversed

    def toggle_reverse(self):
        self._reversed = not self.is_reversed

    def points_w_reversal(self) -> List[PT_Point]:
        return self.points.reversed() if self.is_reversed else self.points

    @property
    def type(self) -> PropType:
        return PT_PointsHolder()
