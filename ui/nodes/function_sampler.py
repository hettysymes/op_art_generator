from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.warp_utils import sample_fun
from ui.port_defs import PortDef, PortType, PT_Function, PT_NumberList

FUN_SAMPLER_NODE = UnitNodeInfo(
    name="Function Sampler",
    resizable=True,
    selectable=False,
    in_port_defs=[PortDef("Function", PT_Function)],
    out_port_defs=[PortDef("Samples", PT_NumberList)],
    prop_type_list=PropTypeList(
        [
            PropType("num_samples", "int", default_value=5,
                     description="Number of samples to obtain from the function f(x), i.e. x values (between 0 & 1) to input.", min_value=1, display_name="Sample number")
        ]
    ),
    description="Sample a function f(x) at equal intervals in the range x ∈ [0, 1]."
)


class FunSamplerNode(UnitNode):
    UNIT_NODE_INFO = FUN_SAMPLER_NODE

    def compute(self):
        function = self.input_nodes[0].compute()
        if function:
            return sample_fun(function, self.prop_vals['num_samples'])

    def visualise(self, temp_dir, height, wh_ratio):
        samples = self.compute()
        if samples is not None:
            return create_graph_svg(height, wh_ratio, samples, self._return_path(temp_dir), scatter=True)
