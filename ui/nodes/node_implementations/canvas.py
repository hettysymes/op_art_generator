from typing import Optional

from ui.id_datatypes import PropKey
from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps
from ui.nodes.node_implementations.visualiser import get_rectangle
from ui.nodes.nodes import UnitNode
from ui.nodes.prop_defs import PropDef, PT_Int, Int, PT_Fill, PT_Element, PortStatus, Colour, PropValue
from ui.nodes.shape_datatypes import Group
from ui.vis_types import Visualisable

DEF_CANVAS_NODE_INFO = PrivateNodeInfo(
    description="Place a drawing on a canvas, where the height and width can be set accurately, as well as the background colour.",
    prop_defs={
        'width': PropDef(
            prop_type=PT_Int(min_value=1, max_value=500),
            display_name="Width (pixels)",
            description="Width of canvas in pixels, set between 1 and 500.",
            default_value=Int(150)
        ),
        'height': PropDef(
            prop_type=PT_Int(min_value=1, max_value=500),
            display_name="Height (pixels)",
            description="Height of canvas in pixels, set between 1 and 500.",
            default_value=Int(150)
        ),
        'bg_fill': PropDef(
            prop_type=PT_Fill(),
            display_name="Background fill",
            description="Background fill of canvas.",
            default_value=Colour(255, 255, 255, 255)
        ),
        'element': PropDef(
            prop_type=PT_Element(),
            display_name="Drawing",
            input_port_status=PortStatus.COMPULSORY
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

    def compute(self, props: ResolvedProps, *args):
        return {'_main': props.get('element'), 'bg_fill': props.get('bg_fill')}

    def visualise(self, compute_results: dict[PropKey, PropValue]) -> Optional[Visualisable]:
        return CanvasNode.helper(compute_results.get('bg_fill'), compute_results.get('_main'))
