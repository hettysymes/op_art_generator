from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.node_info import CHECKERBOARD_NODE_INFO
from ui.nodes.nodes import UnitNode
from ui.nodes.shape import RectangleNode
from ui.nodes.shape_datatypes import Element


class CheckerboardNode(UnitNode):
    UNIT_NODE_INFO = CHECKERBOARD_NODE_INFO

    def compute(self):
        grid_out = self.input_nodes[0].compute()
        element1 = self.input_nodes[1].compute()
        element2 = self.input_nodes[2].compute()
        if grid_out and (element1 or element2):
            default_elem = RectangleNode(None, None, {'fill': 'white'}).compute()
            if not element1:
                element1 = default_elem
            if not element2:
                element2 = default_elem
            v_line_xs, h_line_ys = grid_out
            ret_element = Element()
            element1_starts = True
            for i in range(1, len(v_line_xs)):
                element1_turn = element1_starts
                for j in range(1, len(h_line_ys)):
                    x1 = v_line_xs[i - 1]
                    x2 = v_line_xs[i]
                    y1 = h_line_ys[j - 1]
                    y2 = h_line_ys[j]
                    element = element1 if element1_turn else element2
                    for shape in element:
                        ret_element.add(shape.scale(x2 - x1, y2 - y1).translate(x1, y1))
                    element1_turn = not element1_turn
                element1_starts = not element1_starts
            return ret_element

    def visualise(self, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, element).save()
