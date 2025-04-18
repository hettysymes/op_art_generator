from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.drawers.grid_drawer import GridDrawing
from ui.nodes.grid import GridNode
from ui.nodes.node_info import GRID_NODE_INFO
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape import RectangleNode
from ui.nodes.shape_datatypes import Element
from ui.nodes.warp_utils import PosWarp, RelWarp
from ui.port_defs import PortDef, PortType

COLOUR_LIST_NODE_INFO = UnitNodeInfo(
    name="Colour List",
    resizable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Colours", PortType.VALUE_LIST)],
    prop_type_list=PropTypeList(
        [
            PropType("colours", "colour_table", default_value=["#000000", "#ff0000", "#00ff00", "#0000ff"],
                     description=""),
        ]
    )
)

class ColourListNode(UnitNode):
    UNIT_NODE_INFO = COLOUR_LIST_NODE_INFO

    def compute(self):
        return self.prop_vals['colours']

    def visualise(self, height, wh_ratio):
        colours = self.compute()
        if colours:
            # Draw in vertical grid
            v_line_xs, h_line_ys = GridNode.helper(None, None, 1, len(colours))
            ret_element = Element()
            col_index = 0
            for i in range(1, len(v_line_xs)):
                for j in range(1, len(h_line_ys)):
                    x1 = v_line_xs[i - 1]
                    x2 = v_line_xs[i]
                    y1 = h_line_ys[j - 1]
                    y2 = h_line_ys[j]
                    ret_element.add(RectangleNode(None, None, {'fill': colours[col_index]}).compute()[0].scale(x2 - x1, y2 - y1).translate(x1, y1))
                    col_index += 1
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, ret_element).save()
