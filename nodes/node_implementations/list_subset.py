from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory, DisplayStatus
from nodes.nodes import UnitNode
from nodes.prop_types import PT_Enum, PT_List, PT_Element
from nodes.prop_values import List, Enum

DEF_LIST_SUBSET_INFO = PrivateNodeInfo(
    description="Get a consecutive subset of list.",
    prop_defs={
        'val_list': PropDef(
            prop_type=PT_List(),
            display_name="List",
            description="List to get subset of",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            display_status=DisplayStatus.NO_DISPLAY
        ),
        'start_idx_enum': PropDef(
            prop_type=PT_Enum(),
            display_name="Start index",
            description="Start of list subset.",
            default_value=Enum(),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN
        ),
        'stop_idx_enum': PropDef(
            prop_type=PT_Enum(),
            display_name="Stop index",
            description="Stop of list subset.",
            default_value=Enum(default_first=False),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN
        ),
        '_main': PropDef(
            prop_type=PT_List(),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Subset",
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class ListSubsetNode(UnitNode):
    NAME = "List Subset"
    NODE_CATEGORY = NodeCategory.SELECTOR
    DEFAULT_NODE_INFO = DEF_LIST_SUBSET_INFO

    def compute(self, props: ResolvedProps, *args):
        val_list = props.get('val_list')
        start_enum: Enum = props.get('start_idx_enum')
        stop_enum: Enum = props.get('stop_idx_enum')
        if not val_list:
            start_enum.set_options()
            stop_enum.set_options()
            return {}

        # Update enum
        new_options = list(range(len(val_list)))
        new_display_options = [str(i + 1) for i in new_options]
        start_enum.set_options(new_options, new_display_options)
        stop_enum.set_options(new_options, new_display_options)

        # Get start and stop indices
        start_idx: int = start_enum.selected_option
        stop_idx: int = stop_enum.selected_option
        if start_idx > stop_idx:
            raise ValueError("Start index must be less or equal to stop index")

        subset = [val_list[i] for i in range(start_idx, stop_idx + 1)]
        return {'_main': List(val_list.type, subset)}
