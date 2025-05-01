from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList
from ui.nodes.shape import RectangleNode
from ui.nodes.shape_datatypes import Group
from ui.nodes.transforms import Scale, Translate
from ui.port_defs import PortDef, PT_Grid, PT_Element

CHECKERBOARD_NODE_INFO = UnitNodeInfo(
    name="Checkerboard",
    resizable=True,
    selectable=True,
    in_port_defs=[
        PortDef("Grid", PT_Grid, key_name='grid'),
        PortDef("Drawing 1", PT_Element, key_name='elem1'),
        PortDef("Drawing 2", PT_Element, key_name='elem2')
    ],
    out_port_defs=[PortDef("Drawing", PT_Element)],
    prop_type_list=PropTypeList([]),
    description="Create a checkerboard pattern from a grid and two drawings. The two drawings are placed alternately in a checkerboard pattern on the grid."
)


class CheckerboardNode(UnitNode):
    UNIT_NODE_INFO = CHECKERBOARD_NODE_INFO

    @staticmethod
    def helper(grid, element1=None, element2=None):
        assert element1 or element2
        default_elem = RectangleNode(prop_vals={'fill': (255, 255, 255, 0)}).compute()
        if not element1:
            element1 = default_elem
        if not element2:
            element2 = default_elem
        v_line_xs, h_line_ys = grid
        ret_group = Group(debug_info="Checkerboard")
        element1_starts = True
        for i in range(1, len(v_line_xs)):
            element1_turn = element1_starts
            for j in range(1, len(h_line_ys)):
                x1 = v_line_xs[i - 1]
                x2 = v_line_xs[i]
                y1 = h_line_ys[j - 1]
                y2 = h_line_ys[j]
                element = element1 if element1_turn else element2
                cell_group = Group([Scale(x2 - x1, y2 - y1), Translate(x1, y1)], debug_info=f"Cell ({j},{i})")
                cell_group.add(element)
                ret_group.add(cell_group)
                element1_turn = not element1_turn
            element1_starts = not element1_starts
        return ret_group

    def compute(self):
        grid = self.get_input_node('grid').compute()
        element1 = self.get_input_node('elem1').compute()
        element2 = self.get_input_node('elem2').compute()
        if grid and (element1 or element2):
            return CheckerboardNode.helper(grid, element1, element2)
        return None

    def visualise(self, temp_dir, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (element, None)).save()
        return None
