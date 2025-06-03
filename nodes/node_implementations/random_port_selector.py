from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus
from nodes.nodes import RandomisableNode
from nodes.prop_types import PT_List, PT_ValProbPairHolder
from nodes.prop_values import PropValue, List

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
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Random selection",
            display_in_props=False
        )
    }
)


class RandomPortSelectorNode(RandomisableNode):
    NAME = "Random Port Selector"
    DEFAULT_NODE_INFO = DEF_RANDOM_PORT_SELECTOR_INFO

    def compute(self, props: ResolvedProps, *args):
        val_prob_list: List[PT_ValProbPairHolder] = props.get('val_prob_list')
        if not val_prob_list:
            return {}

        values_weights: list[tuple[PropValue, float]] = [(val_prob.value, val_prob.probability) for val_prob in
                                                         val_prob_list]
        values, weights = zip(*values_weights)
        rng = self.get_random_obj(props.get('seed'))
        return {'_main': rng.choices(list(values), weights=list(weights), k=1)[0]}
