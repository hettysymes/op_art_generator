from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape_datatypes import Element
from ui.port_defs import PortDef, PortType, PT_Element

CANVAS_NODE_INFO = UnitNodeInfo(
    name="Canvas",
    resizable=False,
    selectable=False,
    in_port_defs=[PortDef("Drawing", PT_Element)],
    out_port_defs=[],
    prop_type_list=PropTypeList([
        PropType("width", "int", default_value=150, max_value=500, min_value=1,
                 description=""),
        PropType("height", "int", default_value=150, max_value=500, min_value=1,
                 description=""),
        PropType("bg_col", "colour", default_value=(255, 255, 255, 255),
                 description="", display_name="background colour")
    ]),
    description="Place a drawing on a canvas, where the height and width can be set accurately, as well as the background colour."
)


class CanvasNode(UnitNode):
    UNIT_NODE_INFO = CANVAS_NODE_INFO

    def compute(self):
        return self.input_nodes[0].compute()

    def visualise(self, temp_dir, height, wh_ratio):
        element = self.compute()
        if not element:
            element = Element()
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio,
                             (element, self.prop_vals['bg_col'])).save()
