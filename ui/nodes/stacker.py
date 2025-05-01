from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.grid import GridNode
from ui.nodes.multi_input_handler import handle_multi_inputs
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape_datatypes import Element
from ui.nodes.shape_repeater import ShapeRepeaterNode
from ui.nodes.wrapped_element import WrappedElement
from ui.port_defs import PortDef, PT_Element, PT_Repeatable

STACKER_NODE_INFO = UnitNodeInfo(
    name="Stacker",
    resizable=True,
    selectable=True,
    in_port_defs=[
        PortDef("Input Drawings", PT_Repeatable, input_multiple=True, key_name='repeatables')
    ],
    out_port_defs=[PortDef("Drawing", PT_Element)],
    prop_type_list=PropTypeList([
        PropType("elem_order", "elem_table", default_value=[],
                 description="Order of drawings in which to stack them. Drawings at the top of the list are drawn first (i.e. at the top for vertical stacking, and at the left for horizontal stacking).",
                 display_name="Drawing order"),
        PropType("stack_layout", "enum", default_value="Vertical", options=["Vertical", "Horizontal"],
                 description="Stacking of drawings can be done either top-to-bottom (vertical) or left-to-right (horizontal)",
                 display_name="Stack layout"),
        PropType("wh_diff", "float", default_value=0.4, min_value=0.1,
                 description="Distance to place between stacked drawings, proportional to the height or width of one drawing (height for vertical stacking, width for horizontal stacking). E.g. if set to 0.5, the second drawing will be stacked halfway along the first drawing.",
                 display_name="Height/width distance")
    ]),
    description="Stack multiple drawings together, either vertically or horizontally."
)

class Stack(WrappedElement):

    def __init__(self, elements, wh_diff, vertical_layout):
        self.elements = elements
        self.wh_diff = wh_diff
        self.vertical_layout = vertical_layout

    def element(self):
        n = len(self.elements)
        scale_factor = 1 / self.wh_diff
        scaled_elements = []
        for element in self.elements:
            if self.vertical_layout:
                scaled_elements.append(element.scale(1, scale_factor))
            else:
                scaled_elements.append(element.scale(scale_factor, 1))
        if self.vertical_layout:
            grid = GridNode.helper(None, None, 1, n)
        else:
            grid = GridNode.helper(None, None, n, 1)
        repeated_elem = ShapeRepeaterNode.helper(
            grid,
            scaled_elements
        )
        final_scale_factor = n / (n - 1 + scale_factor)
        if self.vertical_layout:
            return repeated_elem.scale(1, final_scale_factor)
        else:
            return repeated_elem.scale(final_scale_factor, 1)


class StackerNode(UnitNode):
    UNIT_NODE_INFO = STACKER_NODE_INFO

    def compute(self):
        handle_multi_inputs(self.get_input_node('repeatables'), self.prop_vals['elem_order'])
        vertical_layout = self.get_prop_val('stack_layout') == 'Vertical'
        elements = []
        for elem_ref in self.get_prop_val('elem_order'):
            ret_elements = elem_ref.compute()
            if isinstance(ret_elements, Element):
                ret_elements = [ret_elements]
            # Add special case for stack input
            for ret_elem in ret_elements:
                if isinstance(ret_elem, Stack) and ret_elem.vertical_layout == vertical_layout:
                    elements += ret_elem.elements
                else:
                    elements.append(ret_elem)
        if elements:
            return Stack(elements, self.get_prop_val('wh_diff'), vertical_layout)
        return None

    def visualise(self, temp_dir, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (element, None)).save()
        return None
