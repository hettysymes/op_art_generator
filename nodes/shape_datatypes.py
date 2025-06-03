import math
import uuid
from abc import ABC, abstractmethod
from typing import Optional

from nodes.drawers.element_drawer import ElementDrawer
from nodes.prop_types import PT_Ellipse, PT_Polyline, PT_Shape, PT_Polygon, PT_Element, PT_Point
from nodes.prop_values import List, PointsHolder, Point, ElementHolder, Fill, Colour, Gradient
from nodes.transforms import TransformList, Translate, Scale, Rotate
from vis_types import Visualisable


def process_fill(fill: Fill, dwg):
    if isinstance(fill, Gradient):
        colour = fill.get(dwg)
        opacity = 1
    else:
        assert isinstance(fill, Colour)
        colour = fill.colour
        opacity = fill.opacity
    return colour, opacity


class Element(ElementHolder, Visualisable, ABC):

    def __init__(self, debug_info=None):
        self.uid = str(uuid.uuid4())
        self.debug_info = debug_info

    @abstractmethod
    def get(self, dwg):
        pass

    @abstractmethod
    def translate(self, tx, ty):
        pass

    @abstractmethod
    def scale(self, sx, sy):
        pass

    @abstractmethod
    def rotate(self, angle, centre):
        pass

    @abstractmethod
    def shape_transformations(self) -> list[tuple["Shape", TransformList]]:
        pass

    @abstractmethod
    def type(self):
        pass

    @property
    def element(self) -> "Element":
        return self

    def save_to_svg(self, filepath, width, height):
        ElementDrawer(filepath, width, height, self).save()


class Group(Element, PointsHolder):

    def __init__(self, transforms=None, debug_info=None):
        super().__init__(debug_info)
        self.elements = []
        self.transform_list = TransformList(transforms)

    def get(self, dwg):
        transform_str = self.transform_list.get_transform_str()
        if transform_str:
            group = dwg.g(transform=transform_str, id=self.uid)
        else:
            group = dwg.g(id=self.uid)
        for element in self.elements:
            group.add(element.get(dwg))
        return group

    def get_element_index_from_id(self, element_id: str) -> Optional[int]:
        for i, elem in enumerate(self.elements):
            if elem.uid == element_id:
                return i
        return None

    def __iter__(self):
        for element in self.elements:
            yield element

    def __getitem__(self, index):
        return self.elements[index]

    def add(self, element):
        assert isinstance(element, Element)
        self.elements.append(element)

    def translate(self, tx, ty):
        new_group = Group()
        new_group.transform_list.add(Translate(tx, ty))
        if self.elements:
            new_group.add(self)
        return new_group

    def scale(self, sx, sy):
        new_group = Group()
        new_group.transform_list.add(Scale(sx, sy))
        if self.elements:
            new_group.add(self)
        return new_group

    def rotate(self, angle, centre):
        new_group = Group()
        new_group.transform_list.add(Rotate(angle, centre))
        if self.elements:
            new_group.add(self)
        return new_group

    def shape_transformations(self):
        transformed_shapes = []
        for element in self.elements:
            transformed_shapes_prev = element.shape_transformations()
            for shape, transform_list in transformed_shapes_prev:
                new_transform_list = TransformList()
                new_transform_list.transforms = self.transform_list.transforms + transform_list.transforms
                transformed_shapes.append((shape, new_transform_list))
        return transformed_shapes

    @property
    def type(self):
        transformed_shapes = self.shape_transformations()
        if transformed_shapes:
            shapes, _ = zip(*transformed_shapes)
            if len(shapes) == 1:
                return shapes[0].type
        return PT_Element()

    @property
    def points(self) -> List[PT_Point]:
        assert isinstance(self.type, PT_Polyline)
        shape, transform_list = self.shape_transformations()[0]
        if transform_list:
            return transform_list.transform_points(shape.points)
        return shape.points

    def __repr__(self):
        debug_str = f"\"{self.debug_info}\"" if self.debug_info else ""
        result = f"Group ({self.uid}) [{repr(self.transform_list)}] {debug_str} {{\n"
        for elem in self.elements:
            # Get multiline representation and indent each line
            lines = repr(elem).splitlines()
            indented = '\n'.join(f"\t{line}" for line in lines)
            result += f"{indented}\n"
        result += "}"
        return result


class Shape(Element, ABC):

    def translate(self, tx, ty):
        group = Group().translate(tx, ty)
        group.add(self)
        return group

    def scale(self, sx, sy):
        group = Group().scale(sx, sy)
        group.add(self)
        return group

    def rotate(self, angle, centre):
        group = Group().rotate(angle, centre)
        group.add(self)
        return group

    def shape_transformations(self):
        return [(self, TransformList())]

    @property
    def type(self):
        return PT_Shape()

    def __repr__(self):
        return f"Shape ({self.uid}) {self.__class__.__name__.upper()}"


class Polyline(Shape, PointsHolder):

    def __init__(self, points: List[PT_Point], stroke: Fill = Colour(0, 0, 0, 255), stroke_width=1):
        super().__init__()
        self._points = points
        self.stroke = stroke
        self.stroke_width = stroke_width

    @property
    def points(self) -> List[PT_Point]:
        return self._points

    def get(self, dwg):
        stroke, stroke_opacity = process_fill(self.stroke, dwg)
        return dwg.polyline(points=self.points,
                            stroke=stroke,
                            stroke_opacity=stroke_opacity,
                            stroke_width=self.stroke_width,
                            fill='none',
                            style='vector-effect: non-scaling-stroke',
                            id=self.uid)

    @property
    def type(self):
        return PT_Polyline()


class Polygon(Shape):

    def __init__(self, points, fill: Fill, stroke: Fill = Colour(), stroke_width=0):
        super().__init__()
        self.points = points
        self.fill = fill
        self.stroke = stroke
        self.stroke_width = stroke_width

    def get(self, dwg):
        fill, fill_opacity = process_fill(self.fill, dwg)
        stroke, stroke_opacity = process_fill(self.stroke, dwg)
        return dwg.polygon(points=self.points,
                           fill=fill,
                           fill_opacity=fill_opacity,
                           stroke=stroke,
                           stroke_opacity=stroke_opacity,
                           stroke_width=self.stroke_width,
                           style='vector-effect: non-scaling-stroke',
                           id=self.uid)

    @property
    def type(self):
        return PT_Polygon()


class Ellipse(Shape):

    def __init__(self, center, r, fill: Fill, stroke: Fill = Colour(), stroke_width=0):
        super().__init__()
        self.center = center
        self.r = r
        self.fill = fill
        self.stroke = stroke
        self.stroke_width = stroke_width

    def get(self, dwg):
        fill, fill_opacity = process_fill(self.fill, dwg)
        stroke, stroke_opacity = process_fill(self.stroke, dwg)
        return dwg.ellipse(center=self.center,
                           r=self.r,
                           fill=fill,
                           fill_opacity=fill_opacity,
                           stroke=stroke,
                           stroke_opacity=stroke_opacity,
                           stroke_width=self.stroke_width,
                           style='vector-effect: non-scaling-stroke',
                           id=self.uid)

    @property
    def type(self):
        return PT_Ellipse()
