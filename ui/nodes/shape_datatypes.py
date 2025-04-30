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

class Group(Element):

    def __init__(self, transforms=None):
        self.elements = []
        self.transform_list = TransformList(transforms)

    def get(self, dwg):
        group = dwg.g(transform=repr(self.transform_list))
        for element in self.elements:
            group.add(element)
        return group

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

    def __len__(self):
        return len(self.elements)

class Shape(Element, ABC):

    def __init__(self):
        self.shape_id = uuid.uuid4()

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

    def get_points(self):
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
