from typing import Optional

from id_datatypes import PropKey, PortId
from node_graph import RefId
from nodes.drawers.draw_graph import create_graph_svg
from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, Node
from nodes.nodes import UnitNode
from nodes.prop_types import PT_Function, \
    PT_Float, PT_Int, PropType
from nodes.prop_values import PropValue, List, Int, Float
from nodes.warp_datatypes import sample_fun
from vis_types import Visualisable, MatplotlibFig

DEF_RANDOM_ANIMATOR_INFO = PrivateNodeInfo(
    description="Takes a random node as input, and animates a random series of outputs.",
    prop_defs={
        'random_input': PropDef(
            prop_type=PropType(),  # Accept any input (only from one port)
            display_name="Random node",
            input_port_status=PortStatus.COMPULSORY
        ),
        'jump_time': PropDef(
            prop_type=PT_Float(min_value=10),
            display_name="Time between animate change / ms",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN,
            default_value=Float(100)
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Random Output",
            display_in_props=False
        )
    }
)


class RandomAnimatorNode(UnitNode):
    NAME = "Random Animator"
    DEFAULT_NODE_INFO = DEF_RANDOM_ANIMATOR_INFO

    def __init__(self, internal_props: Optional[dict[PropKey, PropValue]] = None, add_info=None):
        self._curr_idx = 0
        self._time_left = 0  # In milliseconds
        self._playing = False
        super().__init__(internal_props, add_info)

    def compute(self, props: ResolvedProps, refs=None, ref_querier=None, *args):
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
        rprops['seed'] = None
        rrefs['seed'] = None
        return {'_main': random_node.final_compute(rprops, rrefs, rquerier)[src_port.key]}

    @property
    def animatable(self) -> bool:
        return True

    @property
    def playing(self) -> bool:
        return self._playing

    def reanimate(self, time: float) -> bool:
        # time is time in milliseconds that has passed
        # Returns True if it moved to the next animation step
        assert self.playing
        self._time_left -= time
        if self._time_left <= 0:
            # Reset time left
            self._time_left: float = self.internal_props['jump_time']  # Time in milliseconds
            return True
        return False

    def toggle_play(self) -> None:
        self._playing = not self._playing
