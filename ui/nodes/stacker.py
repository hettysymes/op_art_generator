import numpy as np

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.function import PiecewiseFunNode
from ui.nodes.grid import GridNode
from ui.nodes.multi_input_handler import handle_multi_inputs
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape_datatypes import Element
from ui.nodes.shape_repeater import ShapeRepeaterNode
from ui.nodes.warp import RelWarpNode
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

    def __init__(self, stack_elem, stack_length, vertical_layout):
        self.stack_elem = stack_elem
        self.stack_length = stack_length
        self.vertical_layout = vertical_layout

    def element(self):
        return self.stack_elem


class StackerNode(UnitNode):
    UNIT_NODE_INFO = STACKER_NODE_INFO

    def compute(self):
        handle_multi_inputs(self.get_input_node('repeatables'), self.prop_vals['elem_order'])
        vertical_layout = self.get_prop_val('stack_layout') == 'Vertical'
        elements = []
        sizes = []
        for elem_ref in self.get_prop_val('elem_order'):
            ret_elements = elem_ref.compute()
            if isinstance(ret_elements, Element):
                ret_elements = [ret_elements]
            # Add special case for stack input
            for ret_elem in ret_elements:
                if isinstance(ret_elem, Stack) and ret_elem.vertical_layout == vertical_layout:
                    sizes.append(ret_elem.stack_length)
                    elements.append(ret_elem.stack_elem)
                else:
                    sizes.append(1)
                    elements.append(ret_elem)
        if elements:
            grid_cell_n = len(elements)
            total_size = sum(sizes)
            scale_factor = 1 /self.get_prop_val('wh_diff')
            scaled_elements = []
            for element in elements:
                if vertical_layout:
                    scaled_elements.append(element.scale(1, scale_factor))
                else:
                    scaled_elements.append(element.scale(scale_factor, 1))
            xs = np.linspace(0, 1, grid_cell_n+1)
            ys = [0] + sizes
            piecewise_f = PiecewiseFunNode.helper(xs, ys)
            rel_warp = RelWarpNode.helper(piecewise_f)
            if vertical_layout:
                grid = GridNode.helper(None, rel_warp, 1, grid_cell_n)
            else:
                grid = GridNode.helper(rel_warp, None, grid_cell_n, 1)
            repeated_elem = ShapeRepeaterNode.helper(
                grid,
                scaled_elements
            )
            final_scale_factor = total_size / (total_size - 1 + scale_factor)
            if vertical_layout:
                final_scaled_elem = repeated_elem.scale(1, final_scale_factor)
            else:
                final_scaled_elem = repeated_elem.scale(final_scale_factor, 1)
            return Stack(final_scaled_elem, total_size, vertical_layout)
        return None

    def visualise(self, temp_dir, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (element, None)).save()
        return None
