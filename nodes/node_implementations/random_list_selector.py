from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory, DisplayStatus
from nodes.nodes import RandomisableNode
from nodes.prop_types import PT_List
from nodes.prop_values import List

DEF_RANDOM_LIST_SELECTOR_INFO = PrivateNodeInfo(
    description="Randomly selects an item from a list input. If multiple inputs are given, then it randomly selects an input.",
    prop_defs={
        'val_list': PropDef(
            prop_type=PT_List(),
            display_name="List",
            description="Input list to select random item of",
            input_port_status=PortStatus.COMPULSORY
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Random selection",
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class RandomListSelectorNode(RandomisableNode):
    NAME = "Random List Selector"
    NODE_CATEGORY = NodeCategory.SELECTOR
    DEFAULT_NODE_INFO = DEF_RANDOM_LIST_SELECTOR_INFO

    def compute(self, props: ResolvedProps, *args):
        val_list: List = props.get('val_list')
        if not val_list:
            return {}
        rng = self.get_random_obj(props.get('seed'))
        return {'_main': rng.choice(val_list.items)}
