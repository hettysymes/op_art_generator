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


class Shape(ABC):

    @abstractmethod
    def translate(self, tx, ty):
        pass

    @abstractmethod
    def scale(self, sx, sy):
        pass

    @abstractmethod
    def get(self, dwg):
        pass


class Polygon(Shape):

    def __init__(self, points, fill, stroke):
        self.points = points
        self.fill = fill
        self.stroke = stroke

    def translate(self, tx, ty):
        return Polygon([(x + tx, y + ty) for x, y in self.points],
                       self.fill,
                       self.stroke)

    def scale(self, sx, sy):
        return Polygon([(x * sx, y * sy) for x, y in self.points],
                       self.fill,
                       self.stroke)

    def get(self, dwg):
        return dwg.polygon(points=self.points,
                           fill=self.fill,
                           stroke=self.stroke)


class Ellipse(Shape):

    def __init__(self, center, r, fill, stroke):
        self.center = center
        self.r = r
        self.fill = fill
        self.stroke = stroke

    def translate(self, tx, ty):
        return Ellipse((self.center[0] + tx, self.center[1] + ty),
                       self.r, self.fill, self.stroke)

    def scale(self, sx, sy):
        return Ellipse((self.center[0] * sx, self.center[1] * sy), (self.r[0] * sx, self.r[1] * sy), self.fill,
                       self.stroke)

    def get(self, dwg):
        return dwg.ellipse(center=self.center,
                           r=self.r,
                           fill=self.fill,
                           stroke=self.stroke)


class SineWave(Shape):

    def __init__(self, amplitude, wavelength, centre_y, phase, x_min, x_max, stroke_width):
        self.amplitude = amplitude
        self.wavelength = wavelength
        self.centre_y = centre_y
        self.phase = phase
        self.x_min = x_min
        self.x_max = x_max
        self.stroke_width = stroke_width

    def translate(self, tx, ty):
        return SineWave(self.amplitude, self.wavelength,
                        self.centre_y + ty, self.phase,
                        self.x_min + tx, self.x_max + tx, self.stroke_width)

    def scale(self, sx, sy):
        return SineWave(self.amplitude * sy, self.wavelength * sx,
                        self.centre_y * sy, self.phase,
                        self.x_min * sx, self.x_max * sx, self.stroke_width)

    def get(self, dwg):
        num_samples = 100
        points = []

        # Generate 100 evenly spaced x-values between x_min and x_max
        x_values = [self.x_min + i * (self.x_max - self.x_min) / (num_samples - 1) for i in range(num_samples)]

        # Calculate corresponding y-values using the sine wave formula
        for x in x_values:
            # Standard sine wave equation: y = A * sin(2π * x / λ + φ) + centre_y
            # where A is amplitude, λ is wavelength, and φ is phase
            y = self.amplitude * math.sin(2 * math.pi * x / self.wavelength + math.radians(self.phase)) + self.centre_y
            points.append((x, y))

        return dwg.polyline(points=points,
                            stroke='black',
                            stroke_width=self.stroke_width,
                            fill='none')
