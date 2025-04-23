import itertools

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList
from ui.nodes.shape_datatypes import Element
from ui.port_defs import PortDef, PortType

SHAPE_REPEATER_NODE_INFO = UnitNodeInfo(
    name="Shape Repeater",
    resizable=True,
    selectable=True,
    in_port_defs=[
        PortDef("Grid", PortType.GRID),
        PortDef("Drawing", PortType.ELEMENT)
    ],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList([])
)


class ShapeRepeaterNode(UnitNode):
    UNIT_NODE_INFO = SHAPE_REPEATER_NODE_INFO

    @staticmethod
    def helper(grid_out, element):
        if grid_out and element:
            v_line_xs, h_line_ys = grid_out
            ret_element = Element()
            if isinstance(element, Element):
                element = [element]
            element_it = itertools.cycle(element)
            for i in range(1, len(v_line_xs)):
                for j in range(1, len(h_line_ys)):
                    x1 = v_line_xs[i - 1]
                    x2 = v_line_xs[i]
                    y1 = h_line_ys[j - 1]
                    y2 = h_line_ys[j]
                    for shape in next(element_it):
                        ret_element.add(shape.scale(x2 - x1, y2 - y1).translate(x1, y1))
            return ret_element

    def compute(self):
        grid_out = self.input_nodes[0].compute()
        element = self.input_nodes[1].compute()
        return ShapeRepeaterNode.helper(grid_out, element)

    def visualise(self, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (element, None)).save()
