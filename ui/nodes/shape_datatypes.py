import copy
import math
from abc import ABC, abstractmethod


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


class Transformation(ABC):

    @abstractmethod
    def apply(self, base_shape):
        pass


class Translate(Transformation):
    def __init__(self, tx, ty):
        self.tx = tx
        self.ty = ty

    def apply(self, base_shape):
        base_shape.translate(self.tx, self.ty)


class Scale(Transformation):
    def __init__(self, sx, sy):
        self.sx = sx
        self.sy = sy

    def apply(self, base_shape):
        base_shape.scale(self.sx, self.sy)

class Rotate(Transformation):
    def __init__(self, angle, centre):
        self.angle = angle
        self.centre = centre

    def apply(self, base_shape):
        base_shape.rotate(self.angle, self.centre)


class Shape(ABC):

    def __init__(self):
        self.transformations = []

    def translate(self, tx, ty):
        new_obj = copy.deepcopy(self)
        new_obj.transformations.append(Translate(tx, ty))
        return new_obj

    def scale(self, sx, sy):
        new_obj = copy.deepcopy(self)
        new_obj.transformations.append(Scale(sx, sy))
        return new_obj

    def rotate(self, angle, centre):
        new_obj = copy.deepcopy(self)
        new_obj.transformations.append(Rotate(angle, centre))
        return new_obj

    @abstractmethod
    def base_shape(self, dwg):
        pass

    def get(self, dwg):
        base_shape = self.base_shape(dwg)
        for t in reversed(self.transformations):
            t.apply(base_shape)
        return base_shape


class Polygon(Shape):

    def __init__(self, points, fill, stroke):
        super().__init__()
        self.points = points
        self.fill = fill
        self.stroke = stroke

    def base_shape(self, dwg):
        return dwg.polygon(points=self.points,
                           fill=self.fill,
                           stroke=self.stroke)


class Ellipse(Shape):

    def __init__(self, center, r, fill, stroke):
        super().__init__()
        self.center = center
        self.r = r
        self.fill = fill
        self.stroke = stroke

    def base_shape(self, dwg):
        return dwg.ellipse(center=self.center,
                           r=self.r,
                           fill=self.fill,
                           stroke=self.stroke)


class SineWave(Shape):

    def __init__(self, amplitude, wavelength, centre_y, phase, x_min, x_max, stroke_width, orientation, num_points):
        super().__init__()
        self.amplitude = amplitude
        self.wavelength = wavelength
        self.centre_y = centre_y
        self.phase = phase
        self.x_min = x_min
        self.x_max = x_max
        self.stroke_width = stroke_width
        self.transformations.append(Rotate(orientation, (0.5,0.5)))
        self.num_points = num_points

    def base_shape(self, dwg):
        points = []

        # Generate 100 evenly spaced x-values between x_min and x_max
        x_values = [self.x_min + i * (self.x_max - self.x_min) / (self.num_points - 1) for i in range(self.num_points)]

        # Calculate corresponding y-values using the sine wave formula
        for x in x_values:
            # Standard sine wave equation: y = A * sin(2π * x / λ + φ) + centre_y
            # where A is amplitude, λ is wavelength, and φ is phase
            y = self.amplitude * math.sin(2 * math.pi * x / self.wavelength + math.radians(self.phase)) + self.centre_y
            points.append((x, y))

        return dwg.polyline(points=points,
                            stroke='black',
                            stroke_width=self.stroke_width,
                            fill='none',
                            style='vector-effect: non-scaling-stroke')
