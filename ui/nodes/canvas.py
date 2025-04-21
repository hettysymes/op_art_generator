from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape_datatypes import Element
from ui.port_defs import PortDef, PortType

CANVAS_NODE_INFO = UnitNodeInfo(
    name="Canvas",
    resizable=False,
    in_port_defs=[PortDef("Drawing", PortType.VISUALISABLE)],
    out_port_defs=[],
    prop_type_list=PropTypeList([
        PropType("width", "int", default_value=150, max_value=500, min_value=1,
                 description=""),
        PropType("height", "int", default_value=150, max_value=500, min_value=1,
                 description=""),
        PropType("bg_col", "colour", default_value=(255, 255, 255, 255),
                 description="", display_name="background colour")
    ])
)


class CanvasNode(UnitNode):
    UNIT_NODE_INFO = CANVAS_NODE_INFO

    def get_svg_path(self, height, wh_ratio):
        vis = self.visualise(height, wh_ratio)
        if vis: return vis
        # No visualisation, return blank canvas
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (Element(), self.prop_vals['bg_col'])).save()

    def compute(self):
        return self.input_nodes[0].compute()

    def visualise(self, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio,
                                 (element, self.prop_vals['bg_col'])).save()
