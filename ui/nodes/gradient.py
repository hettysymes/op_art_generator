import uuid

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.gradient_datatype import Gradient
# from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape import RectangleNode
from ui.nodes.utils import process_rgb
from ui.port_defs import PortType, PortDef



GRADIENT_NODE_INFO = UnitNodeInfo(
    name="Gradient",
    resizable=True,
    selectable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Gradient", PortType.GRADIENT)],
    prop_type_list=PropTypeList([
        PropType("start_col", "colour", default_value=(255, 255, 255, 0),
                 description="", display_name="start colour"),
        PropType("stop_col", "colour", default_value=(255, 255, 255, 255),
                 description="", display_name="stop colour")
    ])
)


class GradientNode(UnitNode):
    UNIT_NODE_INFO = GRADIENT_NODE_INFO

    def compute(self):
        return Gradient(self.prop_vals['start_col'], self.prop_vals['stop_col'])

    def visualise(self, height, wh_ratio):
        element = RectangleNode(None, [self], {}).compute()
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (element, None)).save()

