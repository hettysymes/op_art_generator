from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory, DisplayStatus
from nodes.nodes import UnitNode
from nodes.prop_types import PT_Enum, PT_List, PT_Element
from nodes.prop_values import List, Enum

DEF_DRAWING_GROUP_SUBSET_INFO = PrivateNodeInfo(
    description="Get a consecutive subset of drawing group.",
    prop_defs={
        'drawing_group': PropDef(
            prop_type=PT_List(PT_Element()),
            display_name="Drawing Group",
            description="Drawing Group to get subset of",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            display_status=DisplayStatus.NO_DISPLAY
        ),
        'start_idx_enum': PropDef(
            prop_type=PT_Enum(),
            display_name="Start index",
            description="Start of drawing group subset.",
            default_value=Enum(),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN
        ),
        'stop_idx_enum': PropDef(
            prop_type=PT_Enum(),
            display_name="Stop index",
            description="Stop of drawing group subset.",
            default_value=Enum(default_first=False),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN
        ),
        '_main': PropDef(
            prop_type=PT_List(),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Drawing Group",
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class DrawingGroupSubsetNode(UnitNode):
    NAME = "Subset Group"
    NODE_CATEGORY = NodeCategory.SELECTOR
    DEFAULT_NODE_INFO = DEF_DRAWING_GROUP_SUBSET_INFO

    def compute(self, props: ResolvedProps, *args):
        drawing_group: List[PT_Element] = props.get('drawing_group')
        start_enum: Enum = props.get('start_idx_enum')
        stop_enum: Enum = props.get('stop_idx_enum')
        if not drawing_group:
            start_enum.set_options()
            stop_enum.set_options()
            return {}

        # Update enum
        new_options = list(range(len(drawing_group)))
        new_display_options = [str(i + 1) for i in new_options]
        start_enum.set_options(new_options, new_display_options)
        stop_enum.set_options(new_options, new_display_options)

        # Get start and stop indices
        start_idx: int = start_enum.selected_option
        stop_idx: int = stop_enum.selected_option
        if start_idx > stop_idx:
            raise ValueError("Start index must be less or equal to stop index")

        subset = [drawing_group[i] for i in range(start_idx, stop_idx + 1)]
        return {'_main': List(PT_Element(), subset)}
