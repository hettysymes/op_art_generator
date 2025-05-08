import itertools

from ui.nodes.node_defs import NodeInfo
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Grid, PT_Repeatable, PT_Element
from ui.nodes.shape_datatypes import Group, Element
from ui.nodes.transforms import Scale, Translate

DEF_SHAPE_REPEATER_NODE_INFO = NodeInfo(
    description="Repeat a drawing in a grid-like structure.",
    port_defs={(PortIO.INPUT, 'grid'): PortDef("Grid", PT_Grid),
               (PortIO.INPUT, 'repeatable'): PortDef("Drawing", PT_Repeatable),
               (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Element)}
)


class ShapeRepeaterNode(UnitNode):
    NAME = "Shape Repeater Node"
    DEFAULT_NODE_INFO = DEF_SHAPE_REPEATER_NODE_INFO

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

    def compute(self, out_port_key='_main'):
        grid = self._prop_val('grid')
        elements = self._prop_val('repeatable')
        if grid and elements:
            return ShapeRepeaterNode.helper(grid, elements)
        return None
