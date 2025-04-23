import copy
import math
import uuid
from abc import ABC, abstractmethod

from ui.nodes.gradient_datatype import Gradient
from ui.nodes.point_ref import PointRef


class Element:

    def __init__(self, shapes=None):
        if shapes:
            assert isinstance(shapes, list)
            assert all(isinstance(s, Shape) for s in shapes)
            self.shapes = shapes
        else:
            self.shapes = []

    def add(self, shape):
        assert isinstance(shape, Shape)
        self.shapes.append(shape)

    def __iter__(self):
        return iter(self.shapes)

    def __getitem__(self, index):
        return self.shapes[index]

    def __len__(self):
        return len(self.shapes)


class Transformation(ABC):

    @abstractmethod
    def apply(self, base_shape):
        pass

    @abstractmethod
    def apply_to_point(self, point):
        pass


class Translate(Transformation):
    def __init__(self, tx, ty):
        self.tx = tx
        self.ty = ty

    def apply(self, base_shape):
        base_shape.translate(self.tx, self.ty)

    def apply_to_point(self, point):
        return point[0] + self.tx, point[1] + self.ty


class Scale(Transformation):
    def __init__(self, sx, sy):
        self.sx = sx
        self.sy = sy

    def apply(self, base_shape):
        base_shape.scale(self.sx, self.sy)

    def apply_to_point(self, point):
        return point[0] * self.sx, point[1] * self.sy


class Rotate(Transformation):
    def __init__(self, angle, centre):
        self.angle = angle
        self.centre = centre

    def apply(self, base_shape):
        base_shape.rotate(self.angle, self.centre)

    def apply_to_point(self, point):
        angle_radians = math.radians(self.angle)

        # Translate point back to origin
        x = point[0] - self.centre[0]
        y = point[1] - self.centre[1]

        # Rotate
        rotated_x = x * math.cos(angle_radians) - y * math.sin(angle_radians)
        rotated_y = x * math.sin(angle_radians) + y * math.cos(angle_radians)

        # Translate point back
        x = rotated_x + self.centre[0]
        y = rotated_y + self.centre[1]
        return x, y


class Shape(ABC):

    def __init__(self):
        self.transformations = []
        self.shape_id = uuid.uuid4()

    def translate(self, tx, ty):
        new_obj = copy.deepcopy(self)
        new_obj.shape_id = uuid.uuid4()
        new_obj.transformations.append(Translate(tx, ty))
        return new_obj

    def scale(self, sx, sy):
        new_obj = copy.deepcopy(self)
        new_obj.shape_id = uuid.uuid4()
        new_obj.transformations.append(Scale(sx, sy))
        return new_obj

    def rotate(self, angle, centre):
        new_obj = copy.deepcopy(self)
        new_obj.shape_id = uuid.uuid4()
        new_obj.transformations.append(Rotate(angle, centre))
        return new_obj

    def remove_final_scale(self):
        assert len(self.transformations) > 0
        assert isinstance(self.transformations[-1], Scale)
        new_obj = copy.deepcopy(self)
        new_obj.shape_id = uuid.uuid4()
        del new_obj.transformations[-1]
        return new_obj

    @abstractmethod
    def base_shape(self, dwg):
        pass

    def get(self, dwg):
        base_shape = self.base_shape(dwg)
        for t in reversed(self.transformations):
            t.apply(base_shape)
        return base_shape


class PolyLine(Shape):

    def __init__(self, points, stroke, stroke_width):
        super().__init__()
        self.points = points
        self.stroke = stroke
        self.stroke_width = stroke_width

    def base_shape(self, dwg):
        return dwg.polyline(points=self.points,
                            stroke=self.stroke,
                            stroke_width=self.stroke_width,
                            fill='none',
                            style='vector-effect: non-scaling-stroke',
                            id=self.shape_id)

    def get_points(self):
        transformed_points = []
        for p in self.points:
            transformed_p = p
            for t in self.transformations:
                transformed_p = t.apply_to_point(transformed_p)
            transformed_points.append(transformed_p)
        return transformed_points


class Polygon(Shape):

    def __init__(self, points, fill, fill_opacity):
        super().__init__()
        self.points = points
        self.fill = fill
        self.fill_opacity = fill_opacity

    def base_shape(self, dwg):
        if isinstance(self.fill, Gradient):
            self.fill = self.fill.get(dwg)
        points = []
        for p in self.points:
            if isinstance(p, PointRef):
                points += p.get_points()
            else:
                points.append(p)
        return dwg.polygon(points=points,
                           fill=self.fill,
                           fill_opacity=self.fill_opacity,
                           stroke='none',
                           id=self.shape_id)

class Ellipse(Shape):

    def __init__(self, center, r, fill, fill_opacity, stroke):
        super().__init__()
        self.center = center
        self.r = r
        self.fill = fill
        self.fill_opacity = fill_opacity
        self.stroke = stroke

    def base_shape(self, dwg):
        if isinstance(self.fill, Gradient):
            self.fill = self.fill.get(dwg)
        return dwg.ellipse(center=self.center,
                           r=self.r,
                           fill=self.fill,
                           fill_opacity=self.fill_opacity,
                           stroke=self.stroke,
                           id=self.shape_id)


class SineWave(PolyLine):

    def __init__(self, amplitude, wavelength, centre_y, phase, x_min, x_max, stroke_width, orientation, num_points):
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
        self.transformations.append(Rotate(orientation, (0.5, 0.5)))
