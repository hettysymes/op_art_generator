import copy

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.grid import GridNode
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType, Node
from ui.nodes.shape_datatypes import Group
from ui.port_defs import PortDef, PortType, PT_Element, PT_ElementList

ITERATOR_SELECTOR_NODE_INFO = UnitNodeInfo(
    name="Iterator Selector",
    resizable=True,
    selectable=False,
    in_port_defs=[PortDef("Iterator", PT_ElementList, key_name='iterator')],
    out_port_defs=[PortDef("Drawing", PT_Element)],
    prop_type_list=PropTypeList(
        [
            PropType("select_idx", "selector_enum",
                     description="Index of the element in the iterator output you'd like to select.", display_name="Select index")
        ]
    ),
    description="Select one of the outputs of an Iterator node by inputting its index."
)


class IteratorSelectorNode(UnitNode):
    UNIT_NODE_INFO = ITERATOR_SELECTOR_NODE_INFO

    def compute(self):
        elements = self.get_input_node('iterator').compute()
        if elements and (self.get_prop_val('select_idx') is not None):
            if self.get_prop_val('select_idx') >= len(elements):
                raise NodeInputException("Select index is greater than number of iterator outputs.", self.node_id)
            return elements[self.get_prop_val('select_idx')]

    def visualise(self, temp_dir, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (element, None)).save()
