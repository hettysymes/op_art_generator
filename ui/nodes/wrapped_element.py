from abc import abstractmethod, ABC

from ui.nodes.shape_datatypes import Element


class WrappedElement(Element, ABC):

    @abstractmethod
    def element(self):
        pass

    def get(self, dwg):
        return self.element().get(dwg)

    def translate(self, tx, ty):
        return self.element().translate(tx, ty)

    def scale(self, sx, sy):
        return self.element().scale(sx, sy)

    def rotate(self, angle, centre):
        return self.element().rotate(angle, centre)

    def transformed_shapes(self):
        return self.element().transformed_shapes()