from ui.nodes.drawers.Drawing import Drawing
from ui.nodes.shape_datatypes import Element


class ErrorDrawer(Drawing):

    def draw(self):
        self.add_bg((255, 0, 0, 255))
