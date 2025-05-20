from ui.nodes.drawers.Drawing import Drawing


class ElementDrawer(Drawing):

    def __init__(self, filepath, width, height, inputs):
        super().__init__(filepath, width, height)
        self.element = inputs

    def draw(self):
        self.dwg.viewbox(0, 0, 1, 1)
        self.dwg_add(self.element.get(self.dwg))
