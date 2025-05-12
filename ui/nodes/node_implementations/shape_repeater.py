import itertools

from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_implementations.port_ref_table_handler import flatten_list, handle_port_ref_table
from ui.nodes.nodes import SelectableNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Grid, PT_Element, PT_List, PropEntry, PT_ElemRefTable
from ui.nodes.shape_datatypes import Group, Element
from ui.nodes.transforms import Scale, Translate

DEF_SHAPE_REPEATER_NODE_INFO = NodeInfo(
    description="Repeat a drawing in a grid-like structure.",
    port_defs={(PortIO.INPUT, 'grid'): PortDef("Grid", PT_Grid()),
               (PortIO.INPUT, 'elements'): PortDef("Drawing", PT_List(PT_Element())),
               (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Element())},
    prop_entries={
        'elem_order': PropEntry(PT_ElemRefTable('elements'),
                                display_name="Drawing repeat order",
                                description="Order of drawings in which to repeat them within the grid. Drawings are cycled through the grid cells row by row.",
                                default_value=[])
    }
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
        for i in range(0, len(h_line_ys) - 1):
            # Add row
            for j in range(0, len(v_line_xs) - 1):
                x1 = v_line_xs[j]
                x2 = v_line_xs[j + 1]
                y1 = h_line_ys[i]
                y2 = h_line_ys[i + 1]
                cell_group = Group([Scale(x2 - x1, y2 - y1), Translate(x1, y1)], debug_info=f"Cell ({i},{j})")
                cell_group.add(next(element_it))
                ret_group.add(cell_group)
        return ret_group

    @staticmethod
    def _compute_cell(i, j, main_group, grid):
        return main_group[ShapeRepeaterNode._grid_dims(grid)[1] * i + j]

    # Returns number of rows, number of cols
    @staticmethod
    def _grid_dims(grid):
        v_line_xs, h_line_ys = grid
        return len(h_line_ys) - 1, len(v_line_xs) - 1

    def compute(self):
        grid = self._prop_val('grid')
        ref_elements = self._prop_val('elements', get_refs=True)
        elements = handle_port_ref_table(ref_elements, self._prop_val('elem_order'))
        if not grid or not elements:
            return
        main_group = ShapeRepeaterNode.helper(grid, elements)
        self.set_compute_result(main_group)
        for port_id in self.extracted_port_ids:
            _, port_key = port_id
            # Compute cell
            _, i, j = port_key.split('_')
            cell_group = ShapeRepeaterNode._compute_cell(int(i), int(j), main_group, grid)
            # Update port output type
            self.get_port_defs()[port_id].port_type = cell_group.get_output_type()
            self.set_compute_result(cell_group, port_key=port_key)

    def extract_element(self, parent_group, element_id):
        elem_index = parent_group.get_element_index_from_id(element_id)
        i, j = divmod(elem_index, ShapeRepeaterNode._grid_dims(self._prop_val('grid'))[1])
        # Add new port definition
        port_id = (PortIO.OUTPUT, f'cell_{i}_{j}')
        port_def = PortDef(f"Cell ({i}, {j})", PT_Element())
        self._add_port(port_id, port_def)
        return port_id

    def _is_port_redundant(self, port_id):
        grid = self._prop_val('grid')
        if not grid:
            return True
        _, port_key = port_id
        _, i, j = port_key.split('_')
        height, width = ShapeRepeaterNode._grid_dims(grid)
        return int(i) >= height or int(j) >= width
