from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.node_defs import NodeInfo
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Function, PT_Float, PT_List, PT_Int, PropEntry
from ui.nodes.warp_utils import sample_fun
from ui.vis_types import MatplotlibFig

DEF_FUN_SAMPLER_INFO = NodeInfo(
    description="Sample a function f(x) at equal intervals in the range x ∈ [0, 1].",
    port_defs={
        (PortIO.INPUT, 'function'): PortDef("Function", PT_Function()),
        (PortIO.OUTPUT, '_main'): PortDef("Samples", PT_List(PT_Float()))
    },
    prop_entries={
        'num_samples': PropEntry(PT_Int(min_value=1),
                                 display_name="Sample number",
                                 description="Number of samples (at least 1) to obtain from the function f(x), i.e. x values (between 0 & 1) to input.",
                                 default_value=5)
    }
)


class FunSamplerNode(UnitNode):
    NAME = "Function Sampler"
    DEFAULT_NODE_INFO = DEF_FUN_SAMPLER_INFO

    @staticmethod
    def helper(function, num_samples):
        return sample_fun(function, num_samples)

    def compute(self):
        function = self._prop_val('function')
        if function:
            self.set_compute_result(FunSamplerNode.helper(function, self._prop_val('num_samples')))

    def visualise(self):
        samples = self.get_compute_result()
        if samples is not None:
            return MatplotlibFig(create_graph_svg(samples, scatter=True))
        return None
