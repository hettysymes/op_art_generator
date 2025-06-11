import copy

from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory, DisplayStatus
from nodes.nodes import RandomisableNode
from nodes.prop_types import PT_List
from nodes.prop_values import List

DEF_RANDOM_LIST_SHUFFLER_INFO = PrivateNodeInfo(
    description="Randomly shuffles a list input.",
    prop_defs={
        'val_list': PropDef(
            prop_type=PT_List(),
            display_name="List",
            description="Input list to shuffle.",
            input_port_status=PortStatus.COMPULSORY
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Random shuffle",
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class RandomListShufflerNode(RandomisableNode):
    NAME = "Random List Shuffler"
    NODE_CATEGORY = NodeCategory.LIST_MODIFIER
    DEFAULT_NODE_INFO = DEF_RANDOM_LIST_SHUFFLER_INFO

    def compute(self, props: ResolvedProps, *args):
        val_list: List = props.get('val_list')
        if not val_list:
            return {}
        rng = self.get_random_obj(props.get('seed'))
        ret_items = copy.deepcopy(val_list.items)
        rng.shuffle(ret_items)
        return {'_main': List(val_list.item_type, ret_items)}
