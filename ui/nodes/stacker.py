from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.elem_ref import ElemRef
from ui.nodes.ellipse_sampler import EllipseSamplerNode
from ui.nodes.grid import GridNode
from ui.nodes.multi_input_handler import handle_multi_inputs
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape_datatypes import Element, Polyline, Polygon
from ui.nodes.shape_repeater import ShapeRepeaterNode
from ui.nodes.utils import process_rgb
from ui.port_defs import PortType, PortDef, PT_Ellipse, PT_Element, PT_Repeatable

STACKER_NODE_INFO = UnitNodeInfo(
    name="Stacker",
    resizable=True,
    selectable=True,
    in_port_defs=[
        PortDef("Input Drawings", PT_Repeatable, input_multiple=True)
    ],
    out_port_defs=[PortDef("Drawing", PT_Element)],
    prop_type_list=PropTypeList([
        PropType("elem_order", "elem_table", default_value=[],
                 description="Order of drawings in which to stack them. Drawings at the top of the list are drawn first (i.e. at the top for vertical stacking, and at the left for horizontal stacking).",
                 display_name="Drawing order"),
        PropType("stack_layout", "enum", default_value="Vertical", options=["Vertical", "Horizontal"],
                             description="Stacking of drawings can be done either top-to-bottom (vertical) or left-to-right (horizontal)",
                             display_name="Stack layout"),
        PropType("wh_diff", "float", default_value=0.3, min_value=0.1,
                            description="Distance to place between stacked drawings, proportional to the height or width of one drawing (height for vertical stacking, width for horizontal stacking). E.g. if set to 0.5, the second drawing will be stacked halfway along the first drawing.",
                            display_name="Height/width distance")
    ]),
    description="Stack multiple drawings together, either vertically or horizontally."
)


class StackerNode(UnitNode):
    UNIT_NODE_INFO = STACKER_NODE_INFO

    def compute(self):
        handle_multi_inputs(self.input_nodes, self.prop_vals['elem_order'])
        scaled_elements = []
        for elem_ref in self.prop_vals['elem_order']:
            elements = elem_ref.compute()
            if isinstance(elements, Element):
                elements = [elements]
            scale_factor = 1/self.prop_vals['wh_diff']
            for element in elements:
                if self.prop_vals['stack_layout'] == "Vertical":
                    scaled_elements.append(element.scale(1, scale_factor))
                else:
                    scaled_elements.append(element.scale(scale_factor, 1))
        if scaled_elements:
            if self.prop_vals['stack_layout'] == "Vertical":
                grid = GridNode.helper(None, None, 1, len(scaled_elements))
            else:
                grid = GridNode.helper(None, None, len(scaled_elements), 1)
            return ShapeRepeaterNode.helper(
                grid,
                scaled_elements
            )


    def visualise(self, temp_dir, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (element, None)).save()
