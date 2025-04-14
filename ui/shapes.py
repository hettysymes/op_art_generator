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
