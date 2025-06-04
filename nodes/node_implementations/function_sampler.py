from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory
from nodes.nodes import UnitNode
from nodes.prop_types import PT_Function, PT_Int, PT_Float, PT_List
from nodes.prop_values import List, Int, Float
from nodes.warp_datatypes import sample_fun

DEF_FUN_SAMPLER_INFO = PrivateNodeInfo(
    description="Sample a function f(x) at equal intervals in the range x ∈ [0, 1].",
    prop_defs={
        'function': PropDef(
            prop_type=PT_Function(),
            display_name="Function",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            display_in_props=False
        ),
        'num_samples': PropDef(
            prop_type=PT_Int(min_value=1),
            display_name="Sample number",
            description="Number of samples (at least 1) to obtain from the function f(x), i.e. x values (between 0 & 1) to input.",
            default_value=Int(5)
        ),
        '_main': PropDef(
            prop_type=PT_List(),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Samples",
            display_in_props=False
        )
    }
)


class FunSamplerNode(UnitNode):
    NAME = "Function Sampler"
    NODE_CATEGORY = NodeCategory.PROPERTY_MODIFIER
    DEFAULT_NODE_INFO = DEF_FUN_SAMPLER_INFO

    @staticmethod
    def helper(function, num_samples):
        samples = sample_fun(function, num_samples)
        min_sample = min(samples)
        max_sample = max(samples)
        return List(PT_Float(min_value=min_sample, max_value=max_sample), [Float(i) for i in samples])

    def compute(self, props: ResolvedProps, *args):
        function = props.get('function')
        if function:
            return {'_main': FunSamplerNode.helper(function, props.get('num_samples'))}
        return {}
