from ui.nodes.drawers.group_drawer import GroupDrawer
from ui.nodes.grid import GridNode
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape import RectangleNode
from ui.nodes.shape_repeater import ShapeRepeaterNode
from ui.port_defs import PortDef, PT_ColourList

COLOUR_LIST_NODE_INFO = UnitNodeInfo(
    name="Colour List",
    out_port_defs=[PortDef("Colours", PT_ColourList)],
    prop_type_list=PropTypeList(
        [
            PropType("colours", "colour_table", default_value=[(0, 0, 0, 255), (255, 0, 0, 255), (0, 255, 0, 255)],
                     description="Colours to populate the colour list.", display_name="Colours"),
        ]
    ),
    description="Define a list of colours. This can be provided as input to an Iterator or a Colour Filler."
)


class ColourListNode(UnitNode):
    UNIT_NODE_INFO = COLOUR_LIST_NODE_INFO

    def compute(self):
        return self.get_prop_val('colours')

    def visualise(self):
        colours = self.compute()
        if colours:
            # Draw in vertical grid
            grid = GridNode.helper(None, None, 1, len(colours))
            elements = [RectangleNode.helper(colour) for colour in colours]
            return ShapeRepeaterNode.helper(grid, elements)
        return None
