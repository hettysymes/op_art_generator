from ui.id_datatypes import PropKey
from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps
from ui.nodes.node_implementations.visualiser import repeat_shapes
from ui.nodes.nodes import UnitNode, SelectableNode
from ui.nodes.prop_defs import PropDef, PT_Grid, PortStatus, PT_Element, PT_List, Grid, List, PT_TableEntry
from ui.nodes.shape_datatypes import Group

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




class ShapeRepeaterNode(SelectableNode):
    NAME = "Shape Repeater"
    DEFAULT_NODE_INFO = DEF_SHAPE_REPEATER_NODE_INFO

    @staticmethod
    def _to_cell_key_and_display(i: int, j: int) -> tuple[str, str]:
        return f'cell_{i}_{j}', f'Cell ({i}, {j})'

    @staticmethod
    def _from_cell_key(cell_key: str) -> tuple[int, int]:
        _, i, j = cell_key.split('_')
        return int(i), int(j)

    def compute(self, props: ResolvedProps, _):
        grid: Grid = props.get('grid')
        elem_entries: List[PT_TableEntry[PT_Element]] = props.get('elements')
        if not grid or not elem_entries:
            return {}
        main_group = repeat_shapes(grid, List(PT_Element(), [elem_entry.data for elem_entry in elem_entries]))
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
