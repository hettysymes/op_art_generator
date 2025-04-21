from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.warp_utils import sample_fun
from ui.port_defs import PortDef, PortType

FUN_SAMPLER_NODE = UnitNodeInfo(
    name="Function Sampler",
    resizable=True,
    in_port_defs=[PortDef("Function", PortType.FUNCTION)],
    out_port_defs=[PortDef("Samples", PortType.VALUE_LIST)],
    prop_type_list=PropTypeList(
        [
            PropType("num_samples", "int", default_value=5,
                     description="", min_value=1, display_name="number of samples")
        ]
    )
)


class FunSamplerNode(UnitNode):
    UNIT_NODE_INFO = FUN_SAMPLER_NODE

    def compute(self):
        function = self.input_nodes[0].compute()
        if function:
            return sample_fun(function, self.prop_vals['num_samples'])

    def visualise(self, height, wh_ratio):
        samples = self.compute()
        if samples is not None:
            return create_graph_svg(height, wh_ratio, samples, f"tmp/{str(self.node_id)}", scatter=True)
