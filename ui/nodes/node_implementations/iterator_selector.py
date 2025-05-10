from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PT_Element, PortDef, PT_List
from ui.nodes.prop_defs import PrT_String, PropEntry

DEF_ITERATOR_SELECTOR_INFO = NodeInfo(
    description="Select one of the outputs of an Iterator node by inputting its index.",
    port_defs={
        (PortIO.INPUT, 'iterator'): PortDef("Iterator", PT_List(PT_Element())),
        (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Element())
    },
    prop_entries={
        'select_idx': PropEntry(PrT_String(),
                                display_name="Select index",
                                description="Index of the element in the iterator output you'd like to select.")
    }
)


class IteratorSelectorNode(UnitNode):
    NAME = "Iterator Selector"
    DEFAULT_NODE_INFO = DEF_ITERATOR_SELECTOR_INFO

    def compute(self, out_port_key="_main"):
        elements = self._prop_val('iterator')
        if elements and (self._prop_val('select_idx') is not None):
            if self._prop_val('select_idx') >= len(elements):
                raise NodeInputException("Select index is greater than number of iterator outputs.", self.uid)
            return elements[self._prop_val('select_idx')]
        return None
