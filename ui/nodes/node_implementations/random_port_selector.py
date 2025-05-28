import random
from typing import cast

from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus
from ui.nodes.nodes import UnitNode
from ui.nodes.prop_types import PT_Int, PT_List, PT_ValProbPairHolder
from ui.nodes.prop_values import PropValue, List

DEF_RANDOM_PORT_SELECTOR_INFO = PrivateNodeInfo(
    description="Randomly selects an item from a list input. If multiple inputs are given, then it randomly selects an input.",
    prop_defs={
        'val_prob_list': PropDef(
            prop_type=PT_List(PT_ValProbPairHolder(), input_multiple=True, extract=False),
            display_name="Nodes",
            description="Input nodes to select randomly.",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            default_value=List(PT_ValProbPairHolder())
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


class RandomPortSelectorNode(UnitNode):
    NAME = "Random Port Selector"
    DEFAULT_NODE_INFO = DEF_RANDOM_PORT_SELECTOR_INFO

    def compute(self, props: ResolvedProps, *args):
        # Get random seed if first time computing
        if props.get('seed') is None:
            self.randomise()

        val_prob_list: List[PT_ValProbPairHolder] = props.get('val_prob_list')
        if not val_prob_list:
            return {}

        values_weights: list[tuple[PropValue, float]] = [(val_prob.value, val_prob.probability) for val_prob in val_prob_list]
        values, weights = zip(*values_weights)
        rng = random.Random(props.get('seed'))
        return {'_main': rng.choices(list(values), weights=list(weights), k=1)[0]}

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
