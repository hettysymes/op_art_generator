from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory, DisplayStatus
from nodes.nodes import UnitNode
from nodes.prop_types import PT_List, PT_Enum, PT_Int
from nodes.prop_values import List, Enum, Int

DEF_LIST_SELECTOR_INFO = PrivateNodeInfo(
    description="Selects an item from a list input given an index",
    prop_defs={
        'val_list': PropDef(
            prop_type=PT_List(),
            display_name="List",
            description="Input list to select item of.",
            input_port_status=PortStatus.COMPULSORY
        ),
        'index': PropDef(
            prop_type=PT_Int(min_value=0),
            display_name="Index",
            description="Index of list item to select.",
            default_value=Int(0)
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
        index: Int = props.get('index')
        if not val_list or len(val_list) <= index:
            return {}
        return {'_main': val_list[index]}
