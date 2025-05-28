from typing import Optional

from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus
from nodes.nodes import UnitNode
from nodes.prop_types import PT_Element, PT_Point
from nodes.prop_values import Point
from nodes.shape_datatypes import Element, Group
from nodes.transforms import Scale, Translate

DEF_DRAWING_CROPPER_INFO = PrivateNodeInfo(
    description="Create a group from input drawings.",
    prop_defs={
        'element': PropDef(
            prop_type=PT_Element(),
            display_name="Drawing",
            description="Order of drawings in the drawing group.",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            display_in_props=False
        ),
        'top_left': PropDef(
            prop_type=PT_Point(),
            display_name="Top-left crop",
            description="The top-left corner of the cropping rectangle over the drawing.",
            default_value=Point(0, 0)
        ),
        'bot_right': PropDef(
            prop_type=PT_Point(),
            display_name="Bottom-right crop.",
            description="The bottom-right corner of the cropping rectangle over the drawing.",
            default_value=Point(1, 1)
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Drawing Group",
            display_in_props=False
        )
    }
)


class DrawingCropperNode(UnitNode):
    NAME = "Drawing Cropper"
    DEFAULT_NODE_INFO = DEF_DRAWING_CROPPER_INFO

    def compute(self, props: ResolvedProps, *args):
        element: Optional[Element] = props.get('element')
        if not element:
            return {}

        # Define crop rectangle
        x_min, y_min = props.get('top_left')
        x_max, y_max = props.get('bot_right')

        # Crop group
        cropped_group = Group([Translate(-x_min, -y_min), Scale(1 / (x_max - x_min), 1 / (y_max - y_min))],
                              debug_info="Cropped Drawing")
        cropped_group.add(element)
        return {'_main': cropped_group}
