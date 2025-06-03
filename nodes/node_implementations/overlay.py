from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory
from nodes.nodes import UnitNode
from nodes.prop_types import PT_List, PT_ElementHolder, PT_Element
from nodes.prop_values import List
from nodes.shape_datatypes import Group

DEF_OVERLAY_INFO = PrivateNodeInfo(
    description="Overlay 2+ drawings and define their order.",
    prop_defs={
        'elements': PropDef(
            prop_type=PT_List(PT_ElementHolder(), input_multiple=True),
            display_name="Drawings",
            description="Input drawings to overlay. Drawings at the top of the table are drawn first (i.e. at the bottom of the final overlayed image).",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            default_value=List(PT_ElementHolder())
        ),
        '_main': PropDef(
            prop_type=PT_Element(),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Drawing",
            display_in_props=False
        )
    }
)


class OverlayNode(UnitNode):
    NAME = "Overlay"
    NODE_CATEGORY = NodeCategory.SHAPE_COMPOUNDER
    DEFAULT_NODE_INFO = DEF_OVERLAY_INFO

    def compute(self, props: ResolvedProps, *args):
        elem_entries: List[PT_ElementHolder] = props.get('elements')
        elements = [elem_entry.element for elem_entry in elem_entries]
        # Return final element
        ret_group = Group(debug_info="Overlay")
        for element in elements:
            ret_group.add(element)
        return {'_main': ret_group}
