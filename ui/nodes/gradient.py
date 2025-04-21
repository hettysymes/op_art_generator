from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.port_defs import PortType, PortDef

GRADIENT_NODE_INFO = UnitNodeInfo(
    name="Gradient",
    resizable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Gradient", PortType.GRADIENT)],
    prop_type_list=PropTypeList([
        PropType("start_col", "colour", default_value=(255, 255, 255, 0),
                 description="", display_name="start colour"),
        PropType("end_col", "colour", default_value=(255, 255, 255, 255),
                 description="", display_name="end colour")
    ])
)


class GradientNode(UnitNode):
    UNIT_NODE_INFO = GRADIENT_NODE_INFO

    def compute(self):
        return

    def visualise(self, height, wh_ratio):
        return
