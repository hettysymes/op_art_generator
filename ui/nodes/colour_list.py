from ui.nodes.drawers.grid_drawer import GridDrawing
from ui.nodes.node_info import GRID_NODE_INFO
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.warp_utils import PosWarp, RelWarp
from ui.port_defs import PortDef, PortType

COLOUR_LIST_NODE_INFO = UnitNodeInfo(
    name="Colour List",
    resizable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Colours", PortType.VALUE_LIST)],
    prop_type_list=PropTypeList(
        [
            PropType("colours", "colour_table", default_value=["#000000"],
                     description=""),
        ]
    )
)

class ColourListNode(UnitNode):
    UNIT_NODE_INFO = COLOUR_LIST_NODE_INFO

    def compute(self):
        return self.prop_vals['colours']

    def visualise(self, height, wh_ratio):
        return
