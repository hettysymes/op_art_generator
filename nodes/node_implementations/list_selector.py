from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory, DisplayStatus
from nodes.nodes import UnitNode
from nodes.prop_types import PT_List, PT_Enum
from nodes.prop_values import List, Enum

DEF_LIST_SELECTOR_INFO = PrivateNodeInfo(
    description="Selects an item from a list input given an index",
    prop_defs={
        'val_list': PropDef(
            prop_type=PT_List(),
            display_name="List",
            description="Input list to select item of.",
            input_port_status=PortStatus.COMPULSORY
        ),
        'idx_enum': PropDef(
            prop_type=PT_Enum(),
            display_name="Index",
            description="Index of list item to select.",
            default_value=Enum(),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Selection",
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class ListSelectorNode(UnitNode):
    NAME = "List Selector"
    NODE_CATEGORY = NodeCategory.SELECTOR
    DEFAULT_NODE_INFO = DEF_LIST_SELECTOR_INFO

    def compute(self, props: ResolvedProps, *args):
        val_list: List = props.get('val_list')
        idx_enum: Enum = props.get('idx_enum')
        if not val_list:
            idx_enum.set_options()
            return {}

        # Update enum
        new_options = list(range(len(val_list)))
        new_display_options = [str(i + 1) for i in new_options]
        idx_enum.set_options(new_options, new_display_options)

        return {'_main': val_list[idx_enum.selected_option]}
