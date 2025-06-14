from typing import cast

from id_datatypes import PortId
from node_graph import RefId
from nodes.node_defs import PrivateNodeInfo, ResolvedProps, ResolvedRefs, RefQuerier, Node, PropDef, PortStatus, \
    NodeCategory, DisplayStatus
from nodes.nodes import RandomisableNode
from nodes.prop_types import PT_Int, PropType, PT_Enum, PT_List, find_closest_common_base
from nodes.prop_values import List, Int, Enum

DEF_RANDOM_ITERATOR_INFO = PrivateNodeInfo(
    description="Create a specified number of random iterations, outputting a drawing.",
    prop_defs={
        'random_input': PropDef(
            prop_type=PropType(),  # Accept any input (only from one port)
            display_name="Random node",
            input_port_status=PortStatus.COMPULSORY
        ),
        'num_iterations': PropDef(
            prop_type=PT_Int(min_value=1),
            display_name="Number of iterations",
            description="Number of random iterations of a node output to create, at least 1.",
            default_value=Int(3)
        ),
        'layout_enum': PropDef(
            prop_type=PT_Enum(),
            display_name="Visualisation layout",
            description="Iterations can be visualised in either a vertical or horizontal layout. This only affects the visualisation for this node and not the output itself.",
            default_value=Enum([True, False], ["Vertical", "Horizontal"]),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN
        ),
        '_main': PropDef(
            prop_type=PT_List(),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Random iterations",
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class RandomIteratorNode(RandomisableNode):
    NAME = "Random Iterator"
    NODE_CATEGORY = NodeCategory.ITERATOR
    DEFAULT_NODE_INFO = DEF_RANDOM_ITERATOR_INFO

    def compute(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier):
        random_input = props.get('random_input')
        if random_input is None:
            return {}
        random_node_ref: RefId = refs.get('random_input')
        src_port: PortId = ref_querier.port(random_node_ref)
        random_node: Node = ref_querier.node_copy(random_node_ref)
        num_iterations: Int = props.get('num_iterations')

        # If input node is not randomisable, just return the input the given number of times
        if not random_node.randomisable:
            return {'_main': List(random_input.type, [random_input for _ in range(num_iterations)])}

        # Get random seeds
        rng = self.get_random_obj(props.get('seed'))
        seeds = [rng.random() for _ in range(num_iterations)]
        rprops, rrefs, rquerier = ref_querier.get_compute_inputs(random_node_ref)

        # Calculate and set random compute result
        items = []
        for seed in seeds:
            rprops['seed'] = seed
            rrefs['seed'] = None
            items.append(random_node.final_compute(rprops, rrefs, rquerier)[src_port.key])
        my_type = random_input.type
        for item in items:
            if not item.type.is_compatible_with(my_type):
                if my_type.is_compatible_with(item.type):
                    my_type = item.type
                else:
                    common_base: type[PropType] = find_closest_common_base([item.type for item in items])
                    my_type = common_base()

        return {'_main': List(item_type=my_type,
                              items=items,
                              vertical_layout=cast(Enum, props.get('layout_enum')).selected_option)}
