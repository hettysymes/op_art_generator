import uuid
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, cast

from ui.nodes.prop_types import PropType, PT_List, PT_Scalar, PT_Int, PT_Float, PT_String, PT_Bool, PT_Enum, \
    PT_Point, PT_PointsHolder, PT_Grid, PT_Element, PT_ElementHolder, PT_FillHolder, PT_Fill, PT_Colour, \
    PT_GradOffset, PT_Gradient, PT_ValProbPairHolder


class PropValue(ABC):

    @property
    @abstractmethod
    def type(self) -> PropType:
        pass


T = TypeVar('T', bound='PropType')


class List(Generic[T], PropValue):
    def __init__(self, item_type: T = PropType(), items: Optional[list[PropValue]] = None, vertical_layout=True):
        self.item_type = item_type
        self.items: list[PropValue] = items if items is not None else []
        self.vertical_layout = vertical_layout

        for item in self.items:
            assert item.type.is_compatible_with(self.item_type)

    @property
    def type(self) -> PropType:
        if isinstance(self.item_type, PT_List):
            return PT_List(
                base_item_type=self.item_type.base_item_type,
                depth=self.item_type.depth + 1
            )
        elif isinstance(self.item_type, PT_Scalar):
            return PT_List(base_item_type=self.item_type, depth=1)
        else:
            raise TypeError(f"Invalid item_type: {type(self.item_type)}")

    @staticmethod
    def build_nested_list(items: list[PropValue], base_item_type: PT_Scalar, depth: int) -> "List":
        nested = items
        for _ in range(depth):
            nested = [List(item_type=base_item_type, items=nested)]
            base_item_type = nested[0].type  # Promote type one level up
        return nested[0]

    @staticmethod
    def flatten(x: PropValue) -> "List":
        if isinstance(x, List):
            flat_items = []
            for item in x.items:
                flat_items.extend(List.flatten(item).items)
            item_type = x.item_type.base_item_type if isinstance(x.item_type, PT_List) else x.item_type
            return List(item_type=item_type, items=flat_items)
        else:
            assert isinstance(x.type, PT_Scalar)
            return List(item_type=x.type, items=[x])

    def extract(self, extract_type: PropType) -> PropValue:
        """
        Normalize shape to match `extract_type` (depth),
        but retain base item type from self.
        """
        # Determine target depth
        target_depth = extract_type.depth if isinstance(extract_type, PT_List) else 0

        # Fully flatten this list
        flat: List = List.flatten(self)

        # Derive base item type from self (more specific)
        self_type = self.type
        assert isinstance(self_type, PT_List)
        base_item_type = self_type.base_item_type

        # If scalar expected, return single scalar value
        if target_depth == 0:
            assert len(flat.items) == 1, f"Expected single scalar, got {len(flat.items)}"
            scalar = flat.items[0]
            assert isinstance(scalar.type, PT_Scalar)
            return scalar

        # Re-nest flat items to match target depth
        return List.build_nested_list(flat.items, base_item_type, target_depth)

    def append(self, item: PropValue) -> None:
        if not item.type.is_compatible_with(self.item_type):
            raise TypeError(f"Invalid type: expected {self.item_type}, got {item.type}")
        self.items.append(item)

    def __add__(self, other: "List") -> "List":
        if not isinstance(other, List):
            return NotImplemented

        # Ensure item types are compatible
        if not (isinstance(self.item_type, type(other.item_type)) and isinstance(other.item_type,
                                                                                 type(self.item_type))):
            raise TypeError(f"Cannot add List with item_type {self.item_type} to List with item_type {other.item_type}")

        return List(
            item_type=self.item_type,
            items=self.items + other.items,
            vertical_layout=self.vertical_layout
        )

    def reversed(self):
        return List(self.item_type, list(reversed(self.items)))

    def delete(self, idx: int):
        del self.items[idx]

    def extend(self, other_list):
        assert isinstance(other_list, List) and other_list.item_type.is_compatible_with(self.item_type)
        self.items += other_list.items

    def __bool__(self):
        return len(self.items) > 0

    def __iter__(self):
        return iter(self.items)

    def __getitem__(self, index: int) -> PropValue:
        return self.items[index]

    def __len__(self) -> int:
        return len(self.items)

    def __repr__(self):
        return f"List({repr(self.item_type)}, items={self.items})"


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


class String(str, PropValue):
    def __new__(cls, value: str):
        return super().__new__(cls, value)

    def __init__(self, value: str):
        self.value = value  # Optional but consistent with other PropValue classes

    @property
    def type(self) -> PropType:
        return PT_String()

    def __str__(self) -> str:
        return self

    def __repr__(self) -> str:
        return f'String("{self}")'


class Bool(PropValue):
    def __init__(self, value: bool):
        self.value = value

    @property
    def type(self) -> PropType:
        return PT_Bool()

    def __bool__(self) -> bool:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f'Bool({self.value})'


class Enum(PropValue):

    def __init__(self, options=None, display_options=None, selected_option=None, default_first=True):
        self._selected_option = selected_option
        self._options = None
        self._display_options = None
        self._default_first = default_first
        self.set_options(options, display_options)

    def set_options(self, options=None, display_options=None):
        if options:
            self._options = options
            if display_options:
                assert len(display_options) == len(options)
            self._display_options = display_options if display_options else options
        else:
            self._options = [None]
            self._display_options = ["[none]"]
        if self._selected_option not in self._options:
            self._selected_option = self._options[0] if self._default_first else self._options[-1]

    @property
    def selected_option(self):
        return self._selected_option

    @property
    def options(self):
        return self._options

    @property
    def display_data_options(self):
        return list(zip(self._display_options, self._options))

    @property
    def type(self) -> PropType:
        return PT_Enum()


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


class PortRefTableEntry(PropValue, ABC):
    def __init__(self, ref, data: PropValue, group_idx: tuple[int, int], deletable: bool = True):
        self.ref = ref
        self.deletable = deletable
        self.group_idx = group_idx  # (index_in_group, total_group_len), index starts from 1
        self.data = data


class ElementHolder(PropValue, ABC):
    @property
    @abstractmethod
    def element(self) -> PT_Element:
        pass

    @property
    def type(self) -> PropType:
        return PT_ElementHolder()


class ElementRef(ElementHolder, PortRefTableEntry):

    def __init__(self, ref, data: ElementHolder, group_idx: tuple[int, int], deletable: bool):
        super().__init__(ref, data, group_idx, deletable)

    @property
    def element(self):
        return cast(ElementHolder, self.data).element

    @property
    def type(self) -> PropType:
        return PT_ElementHolder()


class FillHolder(PropValue, ABC):
    @property
    @abstractmethod
    def fill(self):
        pass

    @property
    def type(self) -> PropType:
        return PT_FillHolder()


class FillRef(FillHolder, PortRefTableEntry):

    def __init__(self, ref, data: FillHolder, group_idx: tuple[int, int], deletable: bool):
        super().__init__(ref, data, group_idx, deletable)

    @property
    def fill(self):
        return cast(FillHolder, self.data).fill

    @property
    def type(self) -> PropType:
        return PT_FillHolder()


class Fill(FillHolder):

    @property
    def fill(self):
        return self

    @property
    def type(self) -> PropType:
        return PT_Fill()


class Colour(tuple, Fill):
    def __new__(cls, red: float = 0, green: float = 0, blue: float = 0, alpha: float = 255):
        return super().__new__(cls, (red, green, blue, alpha))

    def __init__(self, red: float = 0, green: float = 0, blue: float = 0, alpha: float = 255):
        pass  # No need to store attributes separately; values are in the tuple

    def __reduce__(self):
        return self.__class__, (self[0], self[1], self[2], self[3])

    @property
    def colour(self) -> str:
        return f'rgb({self[0]},{self[1]},{self[2]})'

    @property
    def opacity(self) -> float:
        return self[3]/255

    @property
    def type(self) -> PropType:
        return PT_Colour()


class Gradient(Fill):

    def __init__(self, start_coord: Point, end_coord: Point, stops: List[PT_GradOffset]):
        super().__init__()
        self.start_coord = start_coord
        self.end_coord = end_coord
        self.stops = stops # Assume this is sorted by ascending offset

    def get(self, dwg):
        grad_id = str(uuid.uuid4())
        gradient = dwg.linearGradient(id=grad_id, start=self.start_coord, end=self.end_coord)
        for stop in self.stops:
            gradient.add_stop_color(offset=stop.offset, opacity=stop.colour.opacity, color=stop.colour.colour)
        dwg.defs.add(gradient)
        return f'url(#{grad_id})'

    @property
    def type(self) -> PropType:
        return PT_Gradient()


class GradOffset(PropValue):

    def __init__(self, offset: float, colour: Colour):
        self.offset = offset
        self.colour = colour

    @property
    def type(self) -> PropType:
        return PT_GradOffset()

class ValProbPairRef(PortRefTableEntry):

    def __init__(self, ref, data: PropValue, group_idx: tuple[int, int], deletable: bool):
        super().__init__(ref, data, group_idx, deletable)
        self.probability = 1

    @property
    def value(self) -> PropValue:
        return self.data

    @property
    def type(self) -> PropType:
        return PT_ValProbPairHolder()


class LineRef(PointsHolder, PortRefTableEntry):
    def __init__(self, ref, data: PointsHolder, group_idx: tuple[int, int], deletable: bool):
        super().__init__(ref, data, group_idx, deletable)
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
