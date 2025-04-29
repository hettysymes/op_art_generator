import uuid

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.gradient_datatype import Gradient
# from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape import RectangleNode
from ui.nodes.utils import process_rgb
from ui.port_defs import PortType, PortDef, PT_Gradient

GRADIENT_NODE_INFO = UnitNodeInfo(
    name="Gradient",
    resizable=True,
    selectable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Gradient", PT_Gradient)],
    prop_type_list=PropTypeList([
        PropType("start_col", "colour", default_value=(255, 255, 255, 0),
                 description="Starting colour of the gradient.", display_name="Start colour"),
        PropType("stop_col", "colour", default_value=(255, 255, 255, 255),
                 description="Stop colour of the gradient.", display_name="Stop colour")
    ]),
    description="Define a linear gradient. This can be passed to a shape node as its fill."
)


class GradientNode(UnitNode):
    UNIT_NODE_INFO = GRADIENT_NODE_INFO

    def compute(self):
        return Gradient(self.prop_vals['start_col'], self.prop_vals['stop_col'])

    def visualise(self, temp_dir, height, wh_ratio):
        element = RectangleNode(None, {}, {}).compute()
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (element, None)).save()

