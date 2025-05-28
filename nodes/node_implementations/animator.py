from typing import Optional

from id_datatypes import PropKey
from nodes.drawers.draw_graph import create_graph_svg
from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus
from nodes.nodes import UnitNode
from nodes.prop_types import PT_Function, \
    PT_Float, PT_Int
from nodes.prop_values import PropValue, List, Int, Float
from nodes.warp_datatypes import sample_fun
from vis_types import Visualisable, MatplotlibFig

DEF_ANIMATOR_INFO = PrivateNodeInfo(
    description="Animate.",
    prop_defs={
        'function': PropDef(
            prop_type=PT_Function(),
            display_name="Function",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            display_in_props=False
        ),
        'jump_time': PropDef(
            prop_type=PT_Float(min_value=10),
            display_name="Time between animate change / ms",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN,
            default_value=Float(100)
        ),
        'num_samples': PropDef(
            prop_type=PT_Int(min_value=2),
            display_name="Number of Samples",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN,
            default_value=Int(20)
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Function Output",
            display_in_props=False
        )
    }
)


class AnimatorNode(UnitNode):
    NAME = "Function Animator"
    DEFAULT_NODE_INFO = DEF_ANIMATOR_INFO

    def __init__(self, internal_props: Optional[dict[PropKey, PropValue]] = None, add_info=None):
        self._curr_idx = None
        self._right_dir = None
        self._time_left = 0  # In milliseconds
        self._reset_idx()
        self._playing = False
        super().__init__(internal_props, add_info)

    def _reset_idx(self):
        self._curr_idx = 0
        self._right_dir = False

    def compute(self, props: ResolvedProps, *args):
        if props.get('function') is None:
            return {}
        # Reset curr index if necessary
        num_samples: int = props.get('num_samples')
        if self._curr_idx >= num_samples:
            self._reset_idx()

        # Get sample from function
        samples: list[float] = sample_fun(props.get('function'), num_samples)
        samples_propval: List[PT_Float] = List(PT_Float(), [Float(s) for s in samples])
        sample: Float = samples_propval[self._curr_idx]
        return {'_main': Float(sample), 'samples': samples, 'curr_index': Int(self._curr_idx)}

    def visualise(self, compute_results: dict[PropKey, PropValue]) -> Optional[Visualisable]:
        samples = compute_results.get('samples')
        if samples is not None:
            return MatplotlibFig(
                create_graph_svg(samples, scatter=True, highlight_index=compute_results.get('curr_index')))
        return None

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

            # Reverse direction at boundaries
            if self._curr_idx == 0 or self._curr_idx == self.internal_props['num_samples'] - 1:
                self._right_dir = not self._right_dir

            # Update current index based on direction
            self._curr_idx += 1 if self._right_dir else -1
            return True
        return False

    def toggle_play(self) -> None:
        self._playing = not self._playing
