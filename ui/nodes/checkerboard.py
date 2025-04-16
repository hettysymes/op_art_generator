from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, PropTypeList
from ui.nodes.shape_datatypes import Element
from ui.port_defs import PortDef, PortType


class CheckerboardNode(UnitNode):
    DISPLAY = "Checkerboard"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = CheckerboardNode.DISPLAY
        self.resizable = True
        self.in_port_defs = [PortDef("Grid", PortType.GRID), PortDef("Drawing 1", PortType.ELEMENT),
                             PortDef("Drawing 2", PortType.ELEMENT)]
        self.out_port_defs = [PortDef("Drawing", PortType.ELEMENT)]
        self.prop_type_list = PropTypeList([])

    def compute(self):
        grid_out = self.input_nodes[0].compute()
        element1 = self.input_nodes[1].compute()
        element2 = self.input_nodes[2].compute()
        if grid_out and element1 and element2:
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
