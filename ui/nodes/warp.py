from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.nodes import UnitNode, PropTypeList, CombinationNode
from ui.nodes.warp_utils import PosWarp, RelWarp
from ui.port_defs import PortDef, PortType


class PosWarpNode(UnitNode):
    DISPLAY = "Pos Warp"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = PosWarpNode.DISPLAY
        self.resizable = True
        self.in_port_defs = [PortDef("Function", PortType.FUNCTION)]
        self.out_port_defs = [PortDef("Warp", PortType.WARP)]
        self.prop_type_list = PropTypeList([])

    def compute(self):
        f = self.input_nodes[0].compute()
        if f: return PosWarp(f)

    def visualise(self, height, wh_ratio):
        warp = self.compute()
        if warp:
            return create_graph_svg(height, wh_ratio, warp.sample(1000), f"tmp/{str(self.node_id)}")


class RelWarpNode(UnitNode):
    DISPLAY = "Rel Warp"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = RelWarpNode.DISPLAY
        self.resizable = True
        self.in_port_defs = [PortDef("Function", PortType.FUNCTION)]
        self.out_port_defs = [PortDef("Warp", PortType.WARP)]
        self.prop_type_list = PropTypeList([])

    def compute(self):
        f = self.input_nodes[0].compute()
        if f: return RelWarp(f)

    def visualise(self, height, wh_ratio):
        warp = self.compute()
        if warp:
            return create_graph_svg(height, wh_ratio, warp.sample(1000), f"tmp/{str(self.node_id)}")


class WarpNode(CombinationNode):
    DISPLAY = "Warp"
    SELECTIONS = [PosWarpNode, RelWarpNode]

    def __init__(self, node_id, input_nodes, properties, selection_index):
        super().__init__(node_id, input_nodes, properties, selection_index)

    def init_selections(self):
        self.selections = WarpNode.SELECTIONS
