from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_implementations.grid import GridNode
from ui.nodes.node_implementations.port_ref_table_handler import handle_port_ref_table
from ui.nodes.node_implementations.shape_repeater import ShapeRepeaterNode
from ui.nodes.node_implementations.visualiser import get_grid, repeat_shapes, visualise_in_1d_grid
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Element, PT_List, PropEntry, PT_Enum, PT_ElemRefTable

DEF_DRAWING_GROUP_INFO = NodeInfo(
    description="Create a group from input drawings.",
    port_defs={
        (PortIO.INPUT, 'elements'): PortDef("Input Drawings", PT_List(PT_Element())),
        (PortIO.OUTPUT, '_main'): PortDef("Drawing Group", PT_List(PT_Element()))
    },
    prop_entries={
        'elem_order': PropEntry(PT_ElemRefTable('elements'),
                                display_name="Drawing group order",
                                description="Order of drawings in the drawing group.",
                                default_value=[]),
        'vis_layout': PropEntry(PT_Enum(["Vertical", "Horizontal"]),
                                display_name="Visualisation layout",
                                description="Drawings can be visualised in either a vertical or horizontal layout. This only affects the visualisation for this node and not the output itself.",
                                default_value="Vertical")
    }
)


class DrawingGroupNode(UnitNode):
    NAME = "Drawing Group"
    DEFAULT_NODE_INFO = DEF_DRAWING_GROUP_INFO

    def compute(self):
        ref_elements = self._prop_val('elements', get_refs=True)
        elements = handle_port_ref_table(ref_elements, self._prop_val('elem_order'))
        self.set_compute_result(elements)

    def visualise(self):
        elements = self.get_compute_result()
        if elements:
            return visualise_in_1d_grid(elements, is_vertical=self._prop_val('vis_layout') == "Vertical")
        return None
