import random
from typing import Optional

from id_datatypes import PortId, PropKey
from node_graph import RefId
from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, Node, RefQuerier, ResolvedRefs, \
    NodeCategory, DisplayStatus
from nodes.nodes import AnimatableNode
from nodes.prop_types import PropType
from nodes.prop_values import PropValue

DEF_RANDOM_ANIMATOR_INFO = PrivateNodeInfo(
    description="Takes a random node as input, and animates a random series of outputs.",
    prop_defs={
        'random_input': PropDef(
            prop_type=PropType(),  # Accept any input (only from one port)
            display_name="Random node",
            input_port_status=PortStatus.COMPULSORY
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Random Output",
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class RandomAnimatorNode(AnimatableNode):
    NAME = "Random Animator"
    NODE_CATEGORY = NodeCategory.ANIMATOR
    DEFAULT_NODE_INFO = DEF_RANDOM_ANIMATOR_INFO

    def __init__(self, internal_props: Optional[dict[PropKey, PropValue]] = None, add_info=None):
        self._last_seed = random.random()
        super().__init__(internal_props, add_info)

    def compute(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier):
        random_input = props.get('random_input')
        if random_input is None:
            return {}
        random_node_ref: RefId = refs.get('random_input')
        src_port: PortId = ref_querier.port(random_node_ref)
        random_node: Node = ref_querier.node_copy(random_node_ref)

        # If input node is not randomisable, just return the input
        if not random_node.randomisable:
            return {'_main': random_input}

        # Return random result
        rprops, rrefs, rquerier = ref_querier.get_compute_inputs(random_node_ref)
        if self.tick_reanimate():
            self._last_seed = random.random()
        rprops['seed'] = self._last_seed
        rrefs['seed'] = None
        return {'_main': random_node.final_compute(rprops, rrefs, rquerier)[src_port.key]}
