from ui.nodes.gradient_datatype import Gradient
from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_implementations.shape import RectangleNode
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Gradient, PT_Fill, PropEntry
from ui.nodes.shape_datatypes import Group

DEF_GRADIENT_NODE_INFO = NodeInfo(
    description="Define a linear gradient. This can be passed to a shape node as its fill.",
    port_defs={(PortIO.OUTPUT, '_main'): PortDef("Gradient", PT_Gradient())},
    prop_entries={'start_col': PropEntry(PT_Fill(),
                                         display_name="Start colour",
                                         description="Starting colour of the gradient.",
                                         default_value=(255, 255, 255, 0)),
                  'stop_col': PropEntry(PT_Fill(),
                                        display_name="Stop colour",
                                        description="Stop colour of the gradient.",
                                        default_value=(255, 255, 255, 255))}
)


class GradientNode(UnitNode):
    NAME = "Gradient"
    DEFAULT_NODE_INFO = DEF_GRADIENT_NODE_INFO

    def compute(self):
        self.set_compute_result(Gradient(self._prop_val('start_col'), self._prop_val('stop_col')))

    def visualise(self):
        group = Group(debug_info="Gradient")
        group.add(RectangleNode.helper(self.get_compute_result()))
        return group
