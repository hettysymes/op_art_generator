from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.warp_utils import sample_fun
from ui.port_defs import PortDef, PT_Function, PT_NumberList
from ui.vis_types import MatplotlibFig

FUN_SAMPLER_NODE = UnitNodeInfo(
    name="Function Sampler",
    selectable=False,
    in_port_defs=[PortDef("Function", PT_Function, key_name='function')],
    out_port_defs=[PortDef("Samples", PT_NumberList)],
    prop_type_list=PropTypeList(
        [
            PropType("num_samples", "int", default_value=5,
                     description="Number of samples to obtain from the function f(x), i.e. x values (between 0 & 1) to input.",
                     min_value=1, display_name="Sample number")
        ]
    ),
    description="Sample a function f(x) at equal intervals in the range x ∈ [0, 1]."
)


class FunSamplerNode(UnitNode):
    UNIT_NODE_INFO = FUN_SAMPLER_NODE

    @staticmethod
    def helper(function, num_samples):
        return sample_fun(function, num_samples)

    def compute(self):
        function = self.get_input_node('function').compute()
        if function:
            return FunSamplerNode.helper(function, self.get_prop_val('num_samples'))
        return None

    def visualise(self):
        samples = self.compute()
        if samples:
            return MatplotlibFig(create_graph_svg(samples, scatter=True))
        return None
