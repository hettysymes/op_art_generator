from typing import cast

from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory, DisplayStatus
from nodes.nodes import UnitNode
from nodes.prop_types import PT_Enum, PT_ElementHolder, PT_List, PT_Element
from nodes.prop_values import List, Enum

DEF_DRAWING_GROUP_INFO = PrivateNodeInfo(
    description="Create a list from input drawings.",
    prop_defs={
        'elements': PropDef(
            prop_type=PT_List(PT_ElementHolder(), input_multiple=True),
            display_name="Drawings",
            description="Order of drawings in the drawing list.",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            default_value=List(PT_ElementHolder())
        ),
        'layout_enum': PropDef(
            prop_type=PT_Enum(),
            display_name="Visualisation layout",
            description="Drawings can be visualised in either a vertical or horizontal layout. This only affects the visualisation for this node and not the output itself.",
            default_value=Enum([True, False], ["Vertical", "Horizontal"]),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN
        ),
        '_main': PropDef(
            prop_type=PT_List(),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Drawing List",
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class DrawingGroupNode(UnitNode):
    NAME = "Drawing List"
    NODE_CATEGORY = NodeCategory.COLLATOR
    DEFAULT_NODE_INFO = DEF_DRAWING_GROUP_INFO

    def compute(self, props: ResolvedProps, *args):
        elem_entries: List[PT_ElementHolder] = props.get('elements')
        if not elem_entries:
            return {}
        ret_list = List(PT_Element(), [elem_entry.element for elem_entry in elem_entries],
                        vertical_layout=cast(Enum, props.get('layout_enum')).selected_option)
        return {'_main': ret_list}
