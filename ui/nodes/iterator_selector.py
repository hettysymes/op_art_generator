import copy

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.grid import GridNode
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType, Node
from ui.nodes.shape_datatypes import Element
from ui.port_defs import PortDef, PortType, PT_Element, PT_ElementList

ITERATOR_SELECTOR_NODE_INFO = UnitNodeInfo(
    name="Iterator Selector",
    resizable=True,
    selectable=False,
    in_port_defs=[PortDef("Iterator", PT_ElementList)],
    out_port_defs=[PortDef("Drawing", PT_Element)],
    prop_type_list=PropTypeList(
        [
            PropType("select_idx", "int", default_value=0, min_value=0,
                     description="", display_name="select index")
        ]
    ),
    description="Select one of the outputs of an Iterator node by inputting its index."
)


class IteratorSelectorNode(UnitNode):
    UNIT_NODE_INFO = ITERATOR_SELECTOR_NODE_INFO

    def compute(self):
        elements = self.input_nodes[0].compute()
        if elements and self.prop_vals['select_idx'] < len(elements):
            return elements[self.prop_vals['select_idx']]

    def visualise(self, temp_dir, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (element, None)).save()
