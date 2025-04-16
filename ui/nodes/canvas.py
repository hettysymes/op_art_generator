from ui.nodes.nodes import Node, PropType, PropTypeList
from ui.port_defs import PortDef, PortType


class CanvasNode(Node):
    DISPLAY = "Canvas"

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)

    def init_attributes(self):
        self.name = CanvasNode.DISPLAY
        self.resizable = False
        self.in_port_defs = [PortDef("Drawing", PortType.VISUALISABLE)]
        self.out_port_defs = []
        self.prop_type_list = PropTypeList([
            PropType("width", "int", default_value=150, max_value=500, min_value=1,
                     description=""),
            PropType("height", "int", default_value=150, max_value=500, min_value=1,
                     description="")
        ])

    def compute(self):
        return self.input_nodes[0].compute()

    def visualise(self, height, wh_ratio):
        return self.input_nodes[0].visualise(height, wh_ratio)
