from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape_datatypes import Element
from ui.port_defs import PortType, PortDef

OVERLAY_NODE_INFO = UnitNodeInfo(
    name="Overlay",
    resizable=True,
    selectable=True,
    in_port_defs=[
        PortDef("Input Drawings", PortType.ELEMENT, input_multiple=True)
    ],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList([
        PropType("elem_order", "string", default_value="",
                             description="", display_name="drawing order")
    ])
)


class OverlayNode(UnitNode):
    UNIT_NODE_INFO = OVERLAY_NODE_INFO

    @staticmethod
    def helper(elements):
        shapes_list = []
        for elem in elements:
            shapes_list += elem.shapes
        return Element(shapes_list)

    def compute(self):
        if self.input_nodes[0].compute():
            return OverlayNode.helper([elem_node.compute() for elem_node in self.input_nodes])

    def visualise(self, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (element, None)).save()
