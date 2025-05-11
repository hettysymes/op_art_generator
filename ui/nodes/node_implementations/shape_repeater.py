import itertools

from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_implementations.port_ref_table_handler import flatten_list
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
        for i in range(0, len(h_line_ys)-1):
            # Add row
            for j in range(0, len(v_line_xs)-1):
                x1 = v_line_xs[j]
                x2 = v_line_xs[j+1]
                y1 = h_line_ys[i]
                y2 = h_line_ys[i+1]
                cell_group = Group([Scale(x2 - x1, y2 - y1), Translate(x1, y1)], debug_info=f"Cell ({i},{j})")
                cell_group.add(next(element_it))
                ret_group.add(cell_group)
        return ret_group

    def _compute_main(self):
        grid = self._prop_val('grid')
        elem_lists_input = self._prop_val('elements')
        if grid and elem_lists_input:
            elements = flatten_list(elem_lists_input)
            return ShapeRepeaterNode.helper(grid, elements)
        return None

    def _compute_cell(self, i, j, main_group):
        return main_group[self._grid_dims()[1]*i + j]

    # Returns number of rows, number of cols
    def _grid_dims(self):
        v_line_xs, h_line_ys = self._prop_val('grid')
        return len(h_line_ys)-1, len(v_line_xs)-1

    def compute(self):
        self._remove_redundant_ports()
        main_group = self._compute_main()
        self.set_compute_result(main_group)
        for port_id in self.extracted_port_ids:
            _, port_key = port_id
            # Compute cell
            _, i, j = port_key.split('_')
            cell_group = self._compute_cell(int(i), int(j), main_group)
            # Update port output type
            self.get_port_defs()[port_id].port_type = PT_Element(cell_group.get_output_type())
            self.set_compute_result(cell_group, port_key=port_key)

    def extract_element(self, parent_group, element_id):
        elem_index = parent_group.get_element_index_from_id(element_id)
        i, j = divmod(elem_index, self._grid_dims()[1])
        # Add new port definition
        port_id = (PortIO.OUTPUT, f'cell_{i}_{j}')
        port_def = PortDef(f"Cell ({i}, {j})", PT_Element())
        self._add_port(port_id, port_def)
        return port_id

    def _is_port_redundant(self, port_id):
        _, port_key = port_id
        _, i, j = port_key.split('_')
        height, width = self._grid_dims()
        return int(i) >= height or int(j) >= width