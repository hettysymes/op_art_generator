import itertools

from ui.nodes.node_defs import NodeInfo
from ui.nodes.nodes import UnitNode, SelectableNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Grid, PT_Element, PT_List
from ui.nodes.shape_datatypes import Group, Element
from ui.nodes.transforms import Scale, Translate

DEF_SHAPE_REPEATER_NODE_INFO = NodeInfo(
    description="Repeat a drawing in a grid-like structure.",
    port_defs={(PortIO.INPUT, 'grid'): PortDef("Grid", PT_Grid()),
               (PortIO.INPUT, 'elements'): PortDef("Drawing", PT_List(PT_Element())),
               (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Element())}
)


class ShapeRepeaterNode(SelectableNode):
    NAME = "Shape Repeater"
    DEFAULT_NODE_INFO = DEF_SHAPE_REPEATER_NODE_INFO

    @staticmethod
    def helper(grid, elements):
        v_line_xs, h_line_ys = grid
        ret_group = Group(debug_info="Shape Repeater")
        if isinstance(elements, Element):
            # Ensure elements is a list
            elements = [elements]
        element_it = itertools.cycle(elements)
        for i in range(1, len(h_line_ys)):
            # Add row
            for j in range(1, len(v_line_xs)):
                x1 = v_line_xs[j - 1]
                x2 = v_line_xs[j]
                y1 = h_line_ys[i - 1]
                y2 = h_line_ys[i]
                cell_group = Group([Scale(x2 - x1, y2 - y1), Translate(x1, y1)], debug_info=f"Cell ({i},{j})")
                cell_group.add(next(element_it))
                ret_group.add(cell_group)
        return ret_group

    def compute(self, out_port_key='_main'):
        grid = self._prop_val('grid')
        elements = self._prop_val('elements')
        if grid and elements:
            return ShapeRepeaterNode.helper(grid, elements)
        return None

    def extract_element(self, parent_group, element_id):
        v_line_xs, _ = self._prop_val('grid')
        number_rows = len(v_line_xs) - 1
        elem_index = parent_group.get_element_index_from_id(element_id)
        i, j = divmod(elem_index, number_rows)
        # Add new port definition
        port_id = (PortIO.OUTPUT, f'cell_{i}_{j}')
        self.node_info.port_defs[port_id] = PortDef(f"Cell ({i}, {j})", PT_Element())
        return port_id
