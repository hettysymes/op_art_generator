import math
from abc import ABC, abstractmethod

from nodes.prop_types import PT_Point
from nodes.prop_values import List, Point


class Transform(ABC):

    @abstractmethod
    def apply_to_point(self, point: Point) -> Point:
        pass

    @abstractmethod
    def __repr__(self):
        pass


class Translate(Transform):
    def __init__(self, tx, ty):
        self.tx = tx
        self.ty = ty

    def apply_to_point(self, point: Point) -> Point:
        return Point(point[0] + self.tx, point[1] + self.ty)

    def __repr__(self):
        return f"translate({self.tx},{self.ty})"


class Scale(Transform):
    def __init__(self, sx, sy):
        self.sx = sx
        self.sy = sy

    def apply_to_point(self, point: Point) -> Point:
        return Point(point[0] * self.sx, point[1] * self.sy)

    def __repr__(self):
        return f"scale({self.sx},{self.sy})"


class Rotate(Transform):
    def __init__(self, angle, centre):
        self.angle = angle
        self.centre = centre

    def apply_to_point(self, point: Point) -> Point:
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
        return Point(x, y)

    def __repr__(self):
        return f"rotate({self.angle},{self.centre[0]},{self.centre[1]})"


class TransformList:

    def __init__(self, transforms=None):
        if transforms:
            self.transforms = list(reversed(transforms))
        else:
            self.transforms = []

    def __iter__(self):
        # Return transformations in application order
        for transform in reversed(self.transforms):
            yield transform

    def add(self, transform):
        # Transformations are applied right-to-left
        assert isinstance(transform, Transform)
        self.transforms.insert(0, transform)

    def __repr__(self):
        parts = [repr(t) for t in self.transforms]
        return ' '.join(parts)

    def get_transform_str(self):
        if self.transforms:
            return repr(self)
        return None

    def transform_points(self, points: List[PT_Point]) -> List[PT_Point]:
        new_points = List(PT_Point())
        for p in points:
            new_point = p
            for t in self:
                new_point = t.apply_to_point(new_point)
            new_points.append(new_point)
        return new_points
