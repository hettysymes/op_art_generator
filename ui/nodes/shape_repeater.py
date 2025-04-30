import itertools

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList
from ui.nodes.shape_datatypes import Group, Element
from ui.nodes.transforms import Scale, Translate
from ui.port_defs import PortDef, PortType, PT_Grid, PT_Element, PT_Repeatable

SHAPE_REPEATER_NODE_INFO = UnitNodeInfo(
    name="Shape Repeater",
    resizable=True,
    selectable=True,
    in_port_defs=[
        PortDef("Grid", PT_Grid, key_name='grid'),
        PortDef("Drawing", PT_Repeatable, key_name='repeatable')
    ],
    out_port_defs=[PortDef("Drawing", PT_Element)],
    prop_type_list=PropTypeList([]),
    description="Repeat a drawing in a grid-like structure."
)


class ShapeRepeaterNode(UnitNode):
    UNIT_NODE_INFO = SHAPE_REPEATER_NODE_INFO

    @staticmethod
    def helper(grid_out, elements):
        v_line_xs, h_line_ys = grid_out
        ret_group = Group()
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
                cell_group = Group([Translate(x1, y1), Scale(x2 - x1, y2 - y1)])
                cell_group.add(next(element_it))
                ret_group.add(cell_group)
        return ret_group

    def compute(self):
        grid_out = self.get_input_node('grid').compute()
        elements = self.get_input_node('repeatable').compute()
        if grid_out and elements:
            return ShapeRepeaterNode.helper(grid_out, elements)
        return None

    def visualise(self, temp_dir, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (element, None)).save()
        return None
