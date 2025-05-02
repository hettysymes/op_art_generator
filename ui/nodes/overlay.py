from ui.nodes.drawers.group_drawer import GroupDrawer
from ui.nodes.multi_input_handler import handle_multi_inputs
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape_datatypes import Group
from ui.port_defs import PortDef, PT_Element

OVERLAY_NODE_INFO = UnitNodeInfo(
    name="Overlay",
    in_port_defs=[
        PortDef("Input Drawings", PT_Element, input_multiple=True, key_name='elements')
    ],
    out_port_defs=[PortDef("Drawing", PT_Element)],
    prop_type_list=PropTypeList([
        PropType("elem_order", "elem_table", default_value=[],
                 description="Order of drawings in which to overlay them. Drawings at the top of the list are drawn first (i.e. at the bottom of the final overlayed image).",
                 display_name="Drawing order")
    ]),
    description="Overlay 2+ drawings and define their order."
)


class OverlayNode(UnitNode):
    UNIT_NODE_INFO = OVERLAY_NODE_INFO

    def compute(self):
        handle_multi_inputs(self.get_input_node('elements'), self.prop_vals['elem_order'])
        ret_group = Group()
        for elem_ref in self.get_prop_val('elem_order'):
            ret_group.add(elem_ref.compute())
        return ret_group

    def visualise(self, temp_dir, height, wh_ratio):
        element = self.compute()
        return GroupDrawer(self._return_path(temp_dir), height, wh_ratio, (element, None)).save()
