from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList
from ui.nodes.shape import RectangleNode
from ui.nodes.shape_datatypes import Element
from ui.port_defs import PortType, PortDef

CHECKERBOARD_NODE_INFO = UnitNodeInfo(
    name="Checkerboard",
    resizable=True,
    selectable=True,
    in_port_defs=[
        PortDef("Grid", PortType.GRID),
        PortDef("Drawing 1", PortType.ELEMENT),
        PortDef("Drawing 2", PortType.ELEMENT)
    ],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList([])
)


class CheckerboardNode(UnitNode):
    UNIT_NODE_INFO = CHECKERBOARD_NODE_INFO

    def compute(self):
        grid_out = self.input_nodes[0].compute()
        element1 = self.input_nodes[1].compute()
        element2 = self.input_nodes[2].compute()
        if grid_out and (element1 or element2):
            default_elem = RectangleNode(None, [UnitNode(None,None,None)], {'fill': (255, 255, 255, 0)}).compute()
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
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (element, None)).save()
