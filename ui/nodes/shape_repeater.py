from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import PropTypeList, UnitNode
from ui.nodes.shape_datatypes import Element
from ui.port_defs import PortDef, PortType


class ShapeRepeaterNode(UnitNode):
    DISPLAY = "Shape Repeater"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = ShapeRepeaterNode.DISPLAY
        self.resizable = True
        self.in_port_defs = [PortDef("Grid", PortType.GRID), PortDef("Drawing", PortType.ELEMENT)]
        self.out_port_defs = [PortDef("Drawing", PortType.ELEMENT)]
        self.prop_type_list = PropTypeList([])

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
