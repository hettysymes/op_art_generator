from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.elem_ref import ElemRef
from ui.nodes.multi_input_handler import handle_multi_inputs
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
        PropType("elem_order", "elem_table", default_value=[],
                             description="", display_name="drawing order")
    ])
)


class OverlayNode(UnitNode):
    UNIT_NODE_INFO = OVERLAY_NODE_INFO

    def compute(self):
        handle_multi_inputs(self.input_nodes, self.prop_vals['elem_order'])
        # Return element
        shapes_list = []
        for elem_ref in self.prop_vals['elem_order']:
            shapes_list += elem_ref.compute().shapes
        return Element(shapes_list)

    def visualise(self, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (element, None)).save()
