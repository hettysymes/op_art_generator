from ui.nodes.drawers.Drawing import Drawing
from ui.nodes.shape_datatypes import Element


class ElementDrawer(Drawing):

    def __init__(self, out_name, height, wh_ratio, inputs):
        super().__init__(out_name, height, wh_ratio)
        assert isinstance(inputs[0], Element)
        self.element, self.bg_col = inputs

    def draw(self):
        if self.bg_col is not None:
            self.add_bg(self.bg_col)
        for shape in self.element:
            s = shape.scale(self.width, self.height)
            self.selectable_shapes.append(s)
            self.dwg_add(s.get(self.dwg))
