from ui.nodes.node_defs import NodeInfo, PropEntry, PropType
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Element, PT_List
from ui.nodes.shape_datatypes import Group

DEF_OVERLAY_INFO = NodeInfo(
    description="Overlay 2+ drawings and define their order.",
    port_defs={
        (PortIO.INPUT, 'elements'): PortDef("Input Drawings", PT_List(PT_Element())),
        (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Element())
    },
    prop_entries={
        'elem_order': PropEntry(PropType.ELEM_TABLE,
                                display_name="Drawing order",
                                description="Order of drawings in which to overlay them. Drawings at the top of the list are drawn first (i.e. at the bottom of the final overlayed image).",
                                default_value=[])
    }
)


class OverlayNode(UnitNode):
    NAME = "Overlay"
    DEFAULT_NODE_INFO = DEF_OVERLAY_INFO

    def compute(self, out_port_key='_main'):
        elements = self._prop_val('elements')
        if elements:
            self.prop_vals['elem_order'] = self._prop_val('elements')
            ret_group = Group(debug_info="Overlay")
            for element in self._prop_val('elem_order'):
                if element:
                    ret_group.add(element)
            return ret_group
        return None
