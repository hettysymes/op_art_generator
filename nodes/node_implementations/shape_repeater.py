from typing import cast

from id_datatypes import PropKey
from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory, DisplayStatus
from nodes.node_implementations.visualiser import repeat_shapes
from nodes.nodes import SelectableNode
from nodes.prop_types import PT_Grid, PT_Element, PT_List, PT_ElementHolder, PT_Enum, PT_Bool
from nodes.prop_values import List, Enum, Grid, Bool
from nodes.shape_datatypes import Group

# from ui.nodes.nodes import SelectableNode

DEF_SHAPE_REPEATER_NODE_INFO = PrivateNodeInfo(
    description="Repeat a drawing in a grid-like structure.",
    prop_defs={
        'grid': PropDef(
            prop_type=PT_Grid(),
            display_name="Grid",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            display_status=DisplayStatus.NO_DISPLAY
        ),
        'elements': PropDef(
            prop_type=PT_List(PT_ElementHolder(), input_multiple=True),
            display_name="Drawings",
            description="Order of drawings in which to repeat them within the grid. Drawings are cycled through the grid cells row by row.",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            default_value=List(PT_ElementHolder())
        ),
        'row_iter_enum': PropDef(
            prop_type=PT_Enum(),
            display_name="Iteration direction",
            description="Drawings can be placed into the grid either row-by-row or column-by-column.",
            default_value=Enum([True, False], ["Row-by-row", "Column-by-column"]),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN
        ),
        'scale_x': PropDef(
            prop_type=PT_Bool(),
            display_name="Scale X",
            description="If ticked (default), each drawing will be scaled to fit the cell width. Otherwise the width of each drawing will stay the same relative to each other.",
            default_value=Bool(True),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN
        ),
        'scale_y': PropDef(
            prop_type=PT_Bool(),
            display_name="Scale Y",
            description="If ticked (default), each drawing will be scaled to fit the cell height. Otherwise the height of each drawing will stay the same relative to each other.",
            default_value=Bool(True),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN
        ),
        '_main': PropDef(
            prop_type=PT_Element(),
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_status=DisplayStatus.NO_DISPLAY
        ),
    }
)


class ShapeRepeaterNode(SelectableNode):
    NAME = "Grid Repeater"
    NODE_CATEGORY = NodeCategory.SHAPE_COMPOUNDER
    DEFAULT_NODE_INFO = DEF_SHAPE_REPEATER_NODE_INFO

    @staticmethod
    def _to_cell_key_and_display(i: int, j: int) -> tuple[str, str]:
        return f'cell_{i}_{j}', f'Cell ({i}, {j})'

    @staticmethod
    def _from_cell_key(cell_key: str) -> tuple[int, int]:
        _, i, j = cell_key.split('_')
        return int(i), int(j)

    def compute(self, props: ResolvedProps, *args):
        grid: Grid = props.get('grid')
        elem_entries: List[PT_ElementHolder] = props.get('elements')
        if not grid or not elem_entries:
            return {}
        main_group = repeat_shapes(grid, List(PT_Element(), [elem_entry.element for elem_entry in elem_entries]),
                                   row_iter=cast(Enum, props.get('row_iter_enum')).selected_option,
                                   scale_x=bool(props.get('scale_x')), scale_y=bool(props.get('scale_y')))
        ret_result = {'_main': main_group}
        for key in self.extracted_props:
            # Compute cell
            i, j = ShapeRepeaterNode._from_cell_key(key)
            ret_result[key] = main_group[grid.width * i + j]
        return ret_result

    def extract_element(self, props: ResolvedProps, parent_group: Group, element_id: str) -> PropKey:
        elem_index: int = parent_group.get_element_index_from_id(element_id)
        grid: Grid = props.get('grid')
        i, j = divmod(elem_index, grid.width)
        # Add new port definition
        prop_key, prop_display = ShapeRepeaterNode._to_cell_key_and_display(i, j)
        port_def = PropDef(
            prop_type=PT_Element(),
            display_name=prop_display,
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.OPTIONAL
        )
        self._add_prop_def(prop_key, port_def)
        return prop_key

    def _is_port_redundant(self, props: ResolvedProps, key: PropKey) -> bool:
        grid: Grid = props.get('grid')
        if not grid:
            return True
        i, j = ShapeRepeaterNode._from_cell_key(key)
        return i >= grid.height or j >= grid.width
