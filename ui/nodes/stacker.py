from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.elem_ref import ElemRef
from ui.nodes.ellipse_sampler import EllipseSamplerNode
from ui.nodes.multi_input_handler import handle_multi_inputs
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape_datatypes import Element, Polyline, Polygon
from ui.nodes.utils import process_rgb
from ui.port_defs import PortType, PortDef, PT_Ellipse, PT_Element

STACKER_NODE_INFO = UnitNodeInfo(
    name="Stacker",
    resizable=True,
    selectable=True,
    in_port_defs=[
        PortDef("Input Drawings", PT_Element, input_multiple=True)
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
                            description="Distance to place between stacked drawings (height or width for vertical or horizontal stacking respectively).",
                            display_name="Height/width distance")
    ]),
    description="Stack multiple drawings together, either vertically or horizontally."
)


class StackerNode(UnitNode):
    UNIT_NODE_INFO = STACKER_NODE_INFO

    def compute(self):
        handle_multi_inputs(self.input_nodes, self.prop_vals['ellipses'])
        # Return element
        elements = []
        for elem_ref in self.prop_vals['elem_order']:
            elements.append(elem_ref.compute())


    def visualise(self, temp_dir, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (element, None)).save()
