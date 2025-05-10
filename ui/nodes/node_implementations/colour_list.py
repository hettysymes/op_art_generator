from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_implementations.grid import GridNode
from ui.nodes.node_implementations.shape import RectangleNode
from ui.nodes.node_implementations.shape_repeater import ShapeRepeaterNode
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Colour, PT_List
from ui.nodes.prop_defs import PrT_ColourTable, PropEntry

DEF_COLOUR_LIST_INFO = NodeInfo(
    description="Define a list of colours. This can be provided as input to an Iterator or a Colour Filler.",
    port_defs={
        (PortIO.OUTPUT, '_main'): PortDef("Colours", PT_List(PT_Colour()))
    },
    prop_entries={
        'colours': PropEntry(PrT_ColourTable(),
                             display_name="Colours",
                             description="Colours to populate the colour list.",
                             default_value=[(0, 0, 0, 255), (255, 0, 0, 255), (0, 255, 0, 255)])
    }
)


class ColourListNode(UnitNode):
    NAME = "Colour List"
    DEFAULT_NODE_INFO = DEF_COLOUR_LIST_INFO

    def compute(self, out_port_key='_main'):
        return self._prop_val('colours')

    def visualise(self):
        colours = self.compute()
        if colours:
            # Draw in vertical grid
            grid = GridNode.helper(None, None, 1, len(colours))
            elements = [RectangleNode.helper(colour) for colour in colours]
            return ShapeRepeaterNode.helper(grid, elements)
        return None
