from ui.nodes.node_info import CANVAS_NODE_INFO
from ui.nodes.nodes import UnitNode


class CanvasNode(UnitNode):
    UNIT_NODE_INFO = CANVAS_NODE_INFO

    def compute(self):
        return self.input_nodes[0].compute()

    def visualise(self, height, wh_ratio):
        return self.input_nodes[0].visualise(height, wh_ratio)
