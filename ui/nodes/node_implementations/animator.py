from typing import Optional

from ui.id_datatypes import PropKey
from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps
from ui.nodes.nodes import UnitNode
from ui.nodes.prop_defs import PropDef, PortStatus, PT_Function, \
    PT_Float, PT_Int, PropValue, Int, Float
from ui.nodes.warp_datatypes import sample_fun

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
        'speed': PropDef(
            prop_type=PT_Float(min_value=0.5),
            display_name="Speed",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN,
            default_value=Float(1)
        ),
        'num_samples': PropDef(
            prop_type=PT_Int(min_value=1),
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
    NAME = "Animator"
    DEFAULT_NODE_INFO = DEF_ANIMATOR_INFO

    def __init__(self, internal_props: Optional[dict[PropKey, PropValue]] = None, add_info=None):
        self._curr_idx = 0
        self._right_dir = True
        super().__init__(internal_props, add_info)

    def compute(self, props: ResolvedProps, *args):
        if props.get('function') is None:
            return {}
        # Reset curr index if necessary
        num_samples: int = props.get('num_samples')
        if self._curr_idx >= num_samples:
            self._curr_idx = 0

        # Get sample from function
        samples: list[float] = sample_fun(props.get('function'), num_samples)
        sample: float = samples[self._curr_idx]
        assert isinstance(sample, float) and not isinstance(sample, Float)
        ret = {'_main': Float(sample)}

        # Reverse direction at boundaries
        if self._curr_idx == 0 or self._curr_idx == num_samples - 1:
            self._right_dir = not self._right_dir

        # Update current index based on direction
        self._curr_idx += 1 if self._right_dir else -1

        return ret
