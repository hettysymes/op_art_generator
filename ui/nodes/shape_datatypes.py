import math
import uuid
from abc import ABC, abstractmethod

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.gradient_datatype import Gradient
from ui.nodes.prop_defs import PT_Ellipse, PT_Polyline, PT_Shape, PT_Polygon, PT_Element, PropValue
from ui.nodes.transforms import TransformList, Translate, Scale, Rotate
from ui.vis_types import Visualisable


class Element(PropValue, Visualisable, ABC):

    def __init__(self, debug_info=None, uid=None):
        self.uid = uid if uid else str(uuid.uuid4())
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
    def shape_transformations(self):
        pass

    @abstractmethod
    def type(self):
        pass

    def save_to_svg(self, filepath, width, height):
        ElementDrawer(filepath, width, height, self).save()

class Group(Element):

    def __init__(self, transforms=None, debug_info=None, uid=None):
        super().__init__(debug_info, uid)
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

    def get_element_index_from_id(self, element_id):
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
        shapes, _ = zip(*self.shape_transformations())
        if len(shapes) == 1:
            return shapes[0].type
        return PT_Element()

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


class Polyline(Shape):

    def __init__(self, points, stroke, stroke_width):
        super().__init__()
        self.points = points
        self.stroke = stroke
        self.stroke_width = stroke_width

    def get(self, dwg):
        return dwg.polyline(points=self.points,
                            stroke=self.stroke,
                            stroke_width=self.stroke_width,
                            fill='none',
                            style='vector-effect: non-scaling-stroke',
                            id=self.uid)

    def get_points(self, transform_list=None):
        if transform_list:
            return transform_list.transform_points(self.points)
        return self.points

    @property
    def type(self):
        return PT_Polyline()


class Polygon(Shape):

    def __init__(self, points, fill, fill_opacity, stroke='none', stroke_width=1.0):
        super().__init__()
        self.points = points
        self.fill = fill
        self.fill_opacity = fill_opacity
        self.stroke = stroke
        self.stroke_width = stroke_width

    def get(self, dwg):
        fill = self.fill.get(dwg) if isinstance(self.fill, Gradient) else self.fill
        return dwg.polygon(points=self.points,
                           fill=fill,
                           fill_opacity=self.fill_opacity,
                           stroke=self.stroke,
                           stroke_width=self.stroke_width,
                           style='vector-effect: non-scaling-stroke',
                           id=self.uid)

    @property
    def type(self):
        return PT_Polygon()


class Ellipse(Shape):

    def __init__(self, center, r, fill, fill_opacity, stroke, stroke_width):
        super().__init__()
        self.center = center
        self.r = r
        self.fill = fill
        self.fill_opacity = fill_opacity
        self.stroke = stroke
        self.stroke_width = stroke_width

    def get(self, dwg):
        fill = self.fill.get(dwg) if isinstance(self.fill, Gradient) else self.fill
        return dwg.ellipse(center=self.center,
                           r=self.r,
                           fill=fill,
                           fill_opacity=self.fill_opacity,
                           stroke=self.stroke,
                           stroke_width=self.stroke_width,
                           style='vector-effect: non-scaling-stroke',
                           id=self.uid)

    @property
    def type(self):
        return PT_Ellipse()


class SineWave(Polyline):

    def __init__(self, amplitude, wavelength, centre_y, phase, x_min, x_max, stroke_width, num_points):
        if x_min > x_max:
            raise ValueError("Wave start position must be smaller than wave stop position.")
        points = []

        # Generate 100 evenly spaced x-values between x_min and x_max
        x_values = [x_min + i * (x_max - x_min) / (num_points - 1) for i in range(num_points)]

        # Calculate corresponding y-values using the sine wave formula
        for x in x_values:
            # Standard sine wave equation: y = A * sin(2π * x / λ + φ) + centre_y
            # where A is amplitude, λ is wavelength, and φ is phase
            y = amplitude * math.sin(2 * math.pi * x / wavelength + math.radians(phase)) + centre_y
            points.append((x, y))

        super().__init__(points, 'black', stroke_width)
