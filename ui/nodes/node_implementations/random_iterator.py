import random
from typing import cast

from ui.id_datatypes import PortId
from ui.node_graph import RefId
from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps, ResolvedRefs, RefQuerier, Node
from ui.nodes.nodes import UnitNode
from ui.nodes.prop_defs import PropDef, PT_List, PT_Int, Int, PortStatus, List

DEF_RANDOM_ITERATOR_INFO = PrivateNodeInfo(
    description="Create a specified number of random iterations, outputting a drawing.",
    prop_defs={
        'random_input': PropDef(
            prop_type=PT_List(input_multiple=False, depth=None), # Accept any input but only from one port
            display_name="Random node",
            input_port_status=PortStatus.COMPULSORY
        ),
        'num_iterations': PropDef(
            prop_type=PT_Int(min_value=1),
            display_name="Number of iterations",
            description="Number of random iterations of a node output to create, at least 1.",
            default_value=Int(3)
        ),
        'seed': PropDef(
            prop_type=PT_Int(min_value=0),
            display_name="Random seed",
            description="Random seed used."
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Random iterations",
            display_in_props=False
        )
    }
)



class RandomIteratorNode(UnitNode):
    NAME = "Random Iterator"
    DEFAULT_NODE_INFO = DEF_RANDOM_ITERATOR_INFO

    def compute(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier):
        # Get random seed if first time computing
        if props.get('seed') is None:
            self.randomise()

        random_input: List = props.get('random_input')
        if random_input is None:
            return {}
        random_node_ref: RefId = refs.get('random_input')
        src_port: PortId = ref_querier.port(random_node_ref)
        random_node: Node = ref_querier.node_copy(random_node_ref)
        num_iterations: Int = props.get('num_iterations')

        # If input node is not randomisable, just return the input the given number of times
        if not random_node.randomisable:
            compute_result = ref_querier.get_compute_result(random_node_ref)
            print(compute_result)
            print(random_input.item_type)
            return {'_main': List(compute_result.type, [compute_result for _ in range(num_iterations)])}

        # Get random seeds
        rng = random.Random(props.get('seed'))
        seeds = [rng.random() for _ in range(num_iterations)]
        comp_inputs = ref_querier.get_compute_inputs(random_node_ref)

        # Calculate and set random compute result
        outputs = List(random_input.item_type)
        for seed in seeds:
            random_node.randomise(seed)
            outputs.append(random_node.final_compute(*comp_inputs)[src_port.key])
        return {'_main': outputs}

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
