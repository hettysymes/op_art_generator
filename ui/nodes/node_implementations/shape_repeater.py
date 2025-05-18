from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps
from ui.nodes.node_implementations.visualiser import repeat_shapes
from ui.nodes.nodes import UnitNode
from ui.nodes.prop_defs import PropDef, PT_Grid, PortStatus, PT_Element, PT_List, Grid, List, PT_TableEntry

# from ui.nodes.nodes import SelectableNode

DEF_SHAPE_REPEATER_NODE_INFO = PrivateNodeInfo(
    description="Repeat a drawing in a grid-like structure.",
    prop_defs={
        'grid': PropDef(
            prop_type=PT_Grid(),
            display_name="Grid",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            display_in_props=False
        ),
        'elements': PropDef(
            prop_type=PT_List(PT_TableEntry(PT_Element()), input_multiple=True),
            display_name="Drawings",
            description="Order of drawings in which to repeat them within the grid. Drawings are cycled through the grid cells row by row.",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            default_value=List(PT_Element())
        ),
        '_main': PropDef(
            prop_type=PT_Element(),
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_in_props=False
        ),
    }
)




class ShapeRepeaterNode(UnitNode):
    NAME = "Shape Repeater"
    DEFAULT_NODE_INFO = DEF_SHAPE_REPEATER_NODE_INFO

    # @staticmethod
    # def _compute_cell(i, j, main_group, grid):
    #     return main_group[ShapeRepeaterNode._grid_dims(grid)[1] * i + j]
    #
    # # Returns number of rows, number of cols
    # @staticmethod
    # def _grid_dims(grid):
    #     v_line_xs, h_line_ys = grid
    #     return len(h_line_ys) - 1, len(v_line_xs) - 1

    def compute(self, props: ResolvedProps, _):
        grid: Grid = props.get('grid')
        elem_entries: List[PT_TableEntry[PT_Element]] = props.get('elements')
        if not grid or not elem_entries:
            return
        main_group = repeat_shapes(grid, List(PT_Element(), [elem_entry.data for elem_entry in elem_entries]))
        print([elem_entry.data.fill for elem_entry in elem_entries])
        return {'_main': main_group}
        # self.set_compute_result(main_group)
        # for port_id in self.extracted_port_ids:
        #     _, port_key = port_id
        #     # Compute cell
        #     _, i, j = port_key.split('_')
        #     cell_group = ShapeRepeaterNode._compute_cell(int(i), int(j), main_group, grid)
        #     # Update port output type
        #     self.get_port_defs()[port_id].port_type = cell_group.get_output_type()
        #     self.set_compute_result(cell_group, port_key=port_key)

    # def extract_element(self, parent_group, element_id):
    #     elem_index = parent_group.get_element_index_from_id(element_id)
    #     i, j = divmod(elem_index, ShapeRepeaterNode._grid_dims(self._prop_val('grid'))[1])
    #     # Add new port definition
    #     port_id = (PortIO.OUTPUT, f'cell_{i}_{j}')
    #     port_def = PortDef(f"Cell ({i}, {j})", PT_Element())
    #     self._add_port(port_id, port_def)
    #     return port_id
    #
    # def _is_port_redundant(self, port_id):
    #     grid = self._prop_val('grid')
    #     if not grid:
    #         return True
    #     _, port_key = port_id
    #     _, i, j = port_key.split('_')
    #     height, width = ShapeRepeaterNode._grid_dims(grid)
    #     return int(i) >= height or int(j) >= width
