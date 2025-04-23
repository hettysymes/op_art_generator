from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList
from ui.nodes.shape_datatypes import Element
from ui.port_defs import PortType, PortDef

OVERLAY_NODE_INFO = UnitNodeInfo(
    name="Overlay",
    resizable=True,
    selectable=True,
    in_port_defs=[
        PortDef("Back Drawing", PortType.ELEMENT),
        PortDef("Front Drawing", PortType.ELEMENT)
    ],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList([])
)


class OverlayNode(UnitNode):
    UNIT_NODE_INFO = OVERLAY_NODE_INFO

    @staticmethod
    def helper(element1, element2):
        if element1 and element2:
            return Element(element1.shapes + element2.shapes)

    def compute(self):
        element1 = self.input_nodes[0].compute()
        element2 = self.input_nodes[1].compute()
        return OverlayNode.helper(element1, element2)

    def visualise(self, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (element, None)).save()
