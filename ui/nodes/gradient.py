from ui.nodes.drawers.group_drawer import GroupDrawer
from ui.nodes.gradient_datatype import Gradient
# from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape import RectangleNode
from ui.nodes.shape_datatypes import Group
from ui.port_defs import PortDef, PT_Gradient

GRADIENT_NODE_INFO = UnitNodeInfo(
    name="Gradient",
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
        return Gradient(self.get_prop_val('start_col'), self.get_prop_val('stop_col'))

    def visualise(self):
        group = Group(debug_info="Gradient")
        group.add(RectangleNode.helper(self.compute()))
        return group
