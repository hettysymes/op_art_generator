from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape import RectangleNode
from ui.nodes.shape_datatypes import Group
from ui.nodes.utils import process_rgb
from ui.port_defs import PortDef, PT_Element

CANVAS_NODE_INFO = UnitNodeInfo(
    name="Canvas",
    resizable=False,
    selectable=False,
    in_port_defs=[PortDef("Drawing", PT_Element, key_name='element')],
    out_port_defs=[],
    prop_type_list=PropTypeList([
        PropType("width", "int", default_value=150, max_value=500, min_value=1,
                 description="Width of canvas in pixels, set between 1 and 500.", display_name="Width (pixels)"),
        PropType("height", "int", default_value=150, max_value=500, min_value=1,
                 description="Height of canvas in pixels, set between 1 and 500.", display_name="Height (pixels)"),
        PropType("bg_col", "colour", default_value=(255, 255, 255, 255),
                 description="Background colour of canvas.", display_name="Background colour")
    ]),
    description="Place a drawing on a canvas, where the height and width can be set accurately, as well as the background colour."
)


class CanvasNode(UnitNode):
    UNIT_NODE_INFO = CANVAS_NODE_INFO

    @staticmethod
    def helper(bg_fill, bg_opacity, element):
        group = Group(debug_info="Canvas")
        group.add(RectangleNode.helper(bg_fill, bg_opacity))
        if element:
            group.add(element)
        return group

    def compute(self):
        return self.get_input_node('element').compute()

    def visualise(self):
        bg_fill, bg_opacity = process_rgb(self.get_prop_val('bg_col'))
        return CanvasNode.helper(bg_fill, bg_opacity, self.compute())
