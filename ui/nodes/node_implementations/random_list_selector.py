import random
from typing import cast

from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps
from ui.nodes.nodes import UnitNode
from ui.nodes.prop_defs import PropDef, PT_List, PT_Int, PortStatus, List

DEF_RANDOM_LIST_SELECTOR_INFO = PrivateNodeInfo(
    description="Randomly select from a list.",
    prop_defs={
        'val_list': PropDef(
            prop_type=PT_List(input_multiple=False, depth=None),  # None depth indicates not to flatten input List
            display_name="List",
            description="Input list to select random item of",
            input_port_status=PortStatus.COMPULSORY
        ),
        'seed': PropDef(
            prop_type=PT_Int(min_value=0),
            display_name="Random seed",
            description="Random seed used."
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Random selection",
            display_in_props=False
        )
    }
)


class RandomListSelectorNode(UnitNode):
    NAME = "Random List Selector"
    DEFAULT_NODE_INFO = DEF_RANDOM_LIST_SELECTOR_INFO

    def compute(self, props: ResolvedProps, *args):
        # Get random seed if first time computing
        if props.get('seed') is None:
            self.randomise()

        val_list: List = props.get('val_list')
        if val_list is None:
            return {}
        # Return random selection
        rng = random.Random(props.get('seed'))
        return {'_main': rng.choice(val_list.items)}

    # Functions needed for randomisable node # TODO make into interface

    def randomise(self, seed=None):
        min_seed: int = cast(PT_Int, self.prop_defs['seed'].prop_type).min_value
        max_seed: int = cast(PT_Int, self.prop_defs['seed'].prop_type).max_value
        self.internal_props['seed'] = seed if seed is not None else random.randint(min_seed, max_seed)

    def get_seed(self):
        return self.internal_props['seed']

    @property
    def randomisable(self):
        return True
