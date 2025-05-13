from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_implementations.shape import RectangleNode
from ui.nodes.node_implementations.visualiser import get_rectangle
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Element, PT_Int, PropEntry, PT_Fill
from ui.nodes.shape_datatypes import Group

DEF_CANVAS_NODE_INFO = NodeInfo(
    description="Place a drawing on a canvas, where the height and width can be set accurately, as well as the background colour.",
    port_defs={(PortIO.INPUT, 'element'): PortDef("Drawing", PT_Element())},
    prop_entries={
        'width': PropEntry(PT_Int(min_value=1, max_value=500),
                           display_name="Width (pixels)",
                           description="Width of canvas in pixels, set between 1 and 500.",
                           default_value=150),
        'height': PropEntry(PT_Int(min_value=1, max_value=500),
                            display_name="Height (pixels)",
                            description="Height of canvas in pixels, set between 1 and 500.",
                            default_value=150),
        'bg_fill': PropEntry(PT_Fill(),
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
        group.add(get_rectangle(colour))
        if element:
            group.add(element)
        return group

    def compute(self):
        self.set_compute_result(self._prop_val('element'))

    def visualise(self):
        return CanvasNode.helper(self._prop_val('bg_fill'), self.get_compute_result())
