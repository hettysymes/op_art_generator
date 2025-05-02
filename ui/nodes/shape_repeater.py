import itertools

from ui.nodes.nodes import UnitNode, UnitNodeInfo
from ui.nodes.shape_datatypes import Group, Element
from ui.nodes.transforms import Scale, Translate
from ui.port_defs import PortDef, PT_Grid, PT_Element, PT_Repeatable

SHAPE_REPEATER_NODE_INFO = UnitNodeInfo(
    name="Shape Repeater",
    in_port_defs=[
        PortDef("Grid", PT_Grid, key_name='grid'),
        PortDef("Drawing", PT_Repeatable, key_name='repeatable')
    ],
    out_port_defs=[PortDef("Drawing", PT_Element)],
    description="Repeat a drawing in a grid-like structure."
)


class ShapeRepeaterNode(UnitNode):
    UNIT_NODE_INFO = SHAPE_REPEATER_NODE_INFO

    @staticmethod
    def helper(grid, elements):
        v_line_xs, h_line_ys = grid
        ret_group = Group(debug_info="Shape Repeater")
        if isinstance(elements, Element):
            # Ensure elements is a list
            elements = [elements]
        element_it = itertools.cycle(elements)
        for i in range(1, len(v_line_xs)):
            for j in range(1, len(h_line_ys)):
                x1 = v_line_xs[i - 1]
                x2 = v_line_xs[i]
                y1 = h_line_ys[j - 1]
                y2 = h_line_ys[j]
                cell_group = Group([Scale(x2 - x1, y2 - y1), Translate(x1, y1)], debug_info=f"Cell ({j},{i})")
                cell_group.add(next(element_it))
                ret_group.add(cell_group)
        return ret_group

    def compute(self):
        grid = self.get_input_node('grid').compute()
        elements = self.get_input_node('repeatable').compute()
        if grid and elements:
            return ShapeRepeaterNode.helper(grid, elements)
        return None
