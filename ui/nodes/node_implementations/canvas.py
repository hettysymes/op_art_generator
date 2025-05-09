from ui.nodes.node_defs import NodeInfo, PropEntry, PropType
from ui.nodes.node_implementations.shape import RectangleNode
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Element
from ui.nodes.shape_datatypes import Group

DEF_CANVAS_NODE_INFO = NodeInfo(
    description="Place a drawing on a canvas, where the height and width can be set accurately, as well as the background colour.",
    port_defs={(PortIO.INPUT, 'element'): PortDef("Drawing", PT_Element())},
    prop_entries={
        'width': PropEntry(PropType.INT,
                           display_name="Width (pixels)",
                           description="Width of canvas in pixels, set between 1 and 500.",
                           default_value=150,
                           min_value=1,
                           max_value=500),
        'height': PropEntry(PropType.INT,
                            display_name="Height (pixels)",
                            description="Height of canvas in pixels, set between 1 and 500.",
                            default_value=150,
                            min_value=1,
                            max_value=500),
        'bg_fill': PropEntry(PropType.FILL,
                             display_name="Background fill",
                             description="Background fill of canvas.",
                             default_value=(255, 255, 255, 255)
                             )
    }
)


class CanvasNode(UnitNode):
    NAME = "Canvas"
    DEFAULT_NODE_INFO = DEF_CANVAS_NODE_INFO

    @staticmethod
    def helper(colour, element=None):
        group = Group(debug_info="Canvas")
        group.add(RectangleNode.helper(colour))
        if element:
            group.add(element)
        return group

    def compute(self, out_port_key='_main'):
        return self._prop_val('element')

    def visualise(self):
        return CanvasNode.helper(self._prop_val('bg_fill'), self.compute())
