import math
from abc import ABC, abstractmethod


class Transform(ABC):

    @abstractmethod
    def apply_to_point(self, point):
        pass

    @abstractmethod
    def __repr__(self):
        pass

class Translate(Transform):
    def __init__(self, tx, ty):
        self.tx = tx
        self.ty = ty

    def apply_to_point(self, point):
        return point[0] + self.tx, point[1] + self.ty

    def __repr__(self):
        return f"translate({self.tx},{self.ty})"

class Scale(Transform):
    def __init__(self, sx, sy):
        self.sx = sx
        self.sy = sy

    def apply_to_point(self, point):
        return point[0] * self.sx, point[1] * self.sy

    def __repr__(self):
        return f"scale({self.sx},{self.sy})"

class Rotate(Transform):
    def __init__(self, angle, centre):
        self.angle = angle
        self.centre = centre

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

    def __repr__(self):
        return f"rotate({self.angle},{self.centre[0]},{self.centre[1]})"


class TransformList:

    def __init__(self, transforms):
        # Transforms at the beginning of the list are applied first
        if transforms:
            assert isinstance(transforms, list)
            assert all(isinstance(t, Transform) for t in transforms)
            self.transforms = transforms
        else:
            self.transforms = []

    def add(self, transform):
        # Adds transform to the beginning of the list
        assert isinstance(transform, Transform)
        self.transforms.insert(0, transform)

    def __repr__(self):
        parts = [repr(t) for t in self.transforms]
        return ' '.join(parts)

    def remove_final_scale(self):
        assert len(self.transforms) > 0
        assert isinstance(self.transforms[0], Scale)
        del self.transforms[0]