from ui.nodes.drawers.Drawing import Drawing
from ui.nodes.shape_datatypes import Group, Element


class ElementDrawer(Drawing):

    def __init__(self, filepath, width, height, inputs):
        super().__init__(filepath, width, height)
        self.element, self.bg_col = inputs
        assert isinstance(self.element, Element)

    def draw(self):
        self.dwg.viewbox(0, 0, 1, 1)
        if self.bg_col is not None:
            self.add_bg(self.bg_col)
        self.dwg_add(self.element.get(self.dwg))
