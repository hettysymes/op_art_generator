from ui.nodes.drawers.Drawing import Drawing
from ui.nodes.shape_datatypes import Element


class ElementDrawer(Drawing):

    def __init__(self, out_name, height, wh_ratio, inputs):
        super().__init__(out_name, height, wh_ratio)
        self.element, self.bg_col = inputs
        assert isinstance(self.element, Element)

    def draw(self):
        if self.bg_col is not None:
            self.add_bg(self.bg_col)
        print(f"INPUT:")
        print(self.element)
        print()
        scaled_elem: Element = self.element.scale(self.width, self.height)
        self.dwg_add(scaled_elem.get(self.dwg))
