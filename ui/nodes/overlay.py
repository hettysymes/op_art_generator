from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.elem_ref import ElemRef
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
        elem_nodes = self.input_nodes
        elem_node_ids = []
        if elem_nodes[0].compute():
            elem_node_ids = [en.node_id for en in elem_nodes]
        indices_to_remove = []
        for i, elem_ref in enumerate(self.prop_vals['elem_order']):
            if elem_ref.node_id in elem_node_ids:
                # Element already exists - mark as not to add
                index = elem_node_ids.index(elem_ref.node_id)
                elem_node_ids[index] = None
            else:
                # Element has been removed
                indices_to_remove.append(i)
        # Remove no longer existing elements
        for i in reversed(indices_to_remove):
            del self.prop_vals['elem_order'][i]
        # Add new elements
        for i, en_id in enumerate(elem_node_ids):
            if en_id is not None:
                self.prop_vals['elem_order'].append(ElemRef(elem_nodes[i]))
        # Return element
        shapes_list = []
        for elem_ref in self.prop_vals['elem_order']:
            shapes_list += elem_ref.compute().shapes
        return Element(shapes_list)

    def visualise(self, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (element, None)).save()
