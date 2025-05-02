from ui.nodes.grid import GridNode
from ui.nodes.multi_input_handler import handle_multi_inputs
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape_repeater import ShapeRepeaterNode
from ui.port_defs import PortDef, PT_Element, PT_ElementList

DRAWING_GROUP_NODE_INFO = UnitNodeInfo(
    name="Drawing Group",
    in_port_defs=[
        PortDef("Input Drawings", PT_Element, input_multiple=True, key_name='elements')
    ],
    out_port_defs=[PortDef("Drawing Group", PT_ElementList)],
    prop_type_list=PropTypeList([
        PropType("elem_order", "elem_table", default_value=[],
                 description="Order of drawings in the drawing group.",
                 display_name="Drawing group order"),
        PropType("vis_layout", "enum", default_value="Vertical", options=["Vertical", "Horizontal"],
                 description="Drawings can be visualised in either a vertical or horizontal layout. This only affects the visualisation for this node and not the output itself.",
                 display_name="Visualisation layout")
    ]),
    description="Create a group from input drawings."
)


class DrawingGroupNode(UnitNode):
    UNIT_NODE_INFO = DRAWING_GROUP_NODE_INFO

    def compute(self):
        handle_multi_inputs(self.get_input_node('elements'), self.prop_vals['elem_order'])
        elements = [elem_ref.compute() for elem_ref in self.get_prop_val('elem_order')]
        return elements

    def visualise(self):
        elements = self.compute()
        if elements:
            if self.get_prop_val('vis_layout') == "Vertical":
                # Draw in vertical grid
                grid = GridNode.helper(None, None, 1, len(elements))
            else:
                # Draw in Horizontal grid
                grid = GridNode.helper(None, None, len(elements), 1)
            return ShapeRepeaterNode.helper(grid, elements)
        return None
