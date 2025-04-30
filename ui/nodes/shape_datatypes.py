import copy
import math
import uuid
from abc import ABC, abstractmethod

from ui.nodes.gradient_datatype import Gradient
from ui.nodes.elem_ref import ElemRef
from ui.nodes.transforms import TransformList, Translate, Scale, Rotate


class Element(ABC):

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
    def transformed_shapes(self):
        pass

class Group(Element):

    def __init__(self):
        self.elements = []
        self.transform_list = TransformList()

    def get(self, dwg):
        transform_str = self.transform_list.get_transform_str()
        if transform_str:
            group = dwg.g(transform=transform_str)
        else:
            group = dwg.g()
        for element in self.elements:
            group.add(element.get(dwg))
        return group

    def add(self, element):
        assert isinstance(element, Element)
        self.elements.append(element)

    def translate(self, tx, ty):
        new_group = copy.deepcopy(self)
        new_group.transform_list.add(Translate(tx, ty))
        return new_group

    def scale(self, sx, sy):
        new_group = copy.deepcopy(self)
        new_group.transform_list.add(Scale(sx, sy))
        return new_group

    def rotate(self, angle, centre):
        new_group = copy.deepcopy(self)
        new_group.transform_list.add(Rotate(angle, centre))
        return new_group

    def remove_final_scale(self):
        new_group = copy.deepcopy(self)
        new_group.transform_list.remove_final_scale()
        return new_group

    def transformed_shapes(self):
        transformed_shapes = []
        for element in self.elements:
            transformed_shapes_prev = element.transformed_shapes()
            for shape, transform_list in transformed_shapes_prev:
                new_transform_list = TransformList()
                new_transform_list.transforms = self.transform_list.transforms + transform_list.transforms
                transformed_shapes.append((shape, new_transform_list))
        return transformed_shapes

class Shape(Element, ABC):

    def __init__(self):
        self.shape_id = uuid.uuid4()

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

    def transformed_shapes(self):
        return [(self, TransformList())]

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
                            id=self.shape_id)

    def get_points(self, transform_list=None):
        if transform_list:
            return transform_list.transform_points(self.points)
        return self.points


class Polygon(Shape):

    def __init__(self, points, fill, fill_opacity, stroke='none', stroke_width=1.0):
        super().__init__()
        self.points = points
        self.fill = fill
        self.fill_opacity = fill_opacity
        self.stroke = stroke
        self.stroke_width = stroke_width

    def get(self, dwg):
        if isinstance(self.fill, Gradient):
            self.fill = self.fill.get(dwg)
        points = []
        for p in self.points:
            if isinstance(p, ElemRef):
                points += p.get_points()
            else:
                points.append(p)
        return dwg.polygon(points=points,
                           fill=self.fill,
                           fill_opacity=self.fill_opacity,
                           stroke=self.stroke,
                           stroke_width=self.stroke_width,
                           style='vector-effect: non-scaling-stroke',
                           id=self.shape_id)

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
        if isinstance(self.fill, Gradient):
            self.fill = self.fill.get(dwg)
        return dwg.ellipse(center=self.center,
                           r=self.r,
                           fill=self.fill,
                           fill_opacity=self.fill_opacity,
                           stroke=self.stroke,
                           stroke_width=self.stroke_width,
                           style='vector-effect: non-scaling-stroke',
                           id=self.shape_id)


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
        # self.transformations.append(Rotate(orientation, (0.5, 0.5)))
