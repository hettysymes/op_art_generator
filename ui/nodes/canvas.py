from ui.nodes.node_info import CANVAS_NODE_INFO
from ui.nodes.nodes import Node, PropType, PropTypeList, UnitNode
from ui.port_defs import PortDef, PortType


class CanvasNode(UnitNode):
    UNIT_NODE_INFO = CANVAS_NODE_INFO

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)

    def compute(self):
        return self.input_nodes[0].compute()

    def visualise(self, height, wh_ratio):
        return self.input_nodes[0].visualise(height, wh_ratio)
