from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.node_info import SHAPE_REPEATER_NODE_INFO
from ui.nodes.nodes import UnitNode
from ui.nodes.shape_datatypes import Element


class ShapeRepeaterNode(UnitNode):
    UNIT_NODE_INFO = SHAPE_REPEATER_NODE_INFO

    def compute(self):
        grid_out = self.input_nodes[0].compute()
        element = self.input_nodes[1].compute()
        if grid_out and element:
            v_line_xs, h_line_ys = grid_out
            ret_element = Element()
            for i in range(1, len(v_line_xs)):
                for j in range(1, len(h_line_ys)):
                    x1 = v_line_xs[i - 1]
                    x2 = v_line_xs[i]
                    y1 = h_line_ys[j - 1]
                    y2 = h_line_ys[j]
                    for shape in element:
                        ret_element.add(shape.scale(x2 - x1, y2 - y1).translate(x1, y1))
            return ret_element

    def visualise(self, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, element).save()
