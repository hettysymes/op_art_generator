from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.node_defs import NodeInfo, PropType, PropEntry
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_NumberList, PT_Function
from ui.nodes.warp_utils import sample_fun
from ui.vis_types import MatplotlibFig

DEF_FUN_SAMPLER_INFO = NodeInfo(
    description="Sample a function f(x) at equal intervals in the range x ∈ [0, 1].",
    port_defs={
        (PortIO.INPUT, 'function'): PortDef("Function", PT_Function),
        (PortIO.OUTPUT, '_main'): PortDef("Samples", PT_NumberList)
    },
    prop_entries={
        'num_samples': PropEntry(PropType.INT,
                                 display_name="Sample number",
                                 description="Number of samples to obtain from the function f(x), i.e. x values (between 0 & 1) to input.",
                                 default_value=5,
                                 min_value=1)
    }
)


class FunSamplerNode(UnitNode):
    NAME = "Function Sampler"
    DEFAULT_NODE_INFO = DEF_FUN_SAMPLER_INFO

    @staticmethod
    def helper(function, num_samples):
        return sample_fun(function, num_samples)

    def compute(self, out_port_key='_main'):
        function = self._prop_val('function')
        if function:
            return FunSamplerNode.helper(function, self._prop_val('num_samples'))
        return None

    def visualise(self):
        samples = self.compute()
        if samples is not None:
            return MatplotlibFig(create_graph_svg(samples, scatter=True))
        return None
