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
        ref_elements = self._prop_val('elements', get_refs=True)
        if not ref_elements: return None

        # Update element order list
        ref_ids_to_add = list(ref_elements.keys())
        indices_to_remove = []
        for i, (ref_id, _) in enumerate(self._prop_val('elem_order')):
            if ref_id in ref_elements:
                # Element already exists - do not add again
                ref_ids_to_add.remove(ref_id)
            else:
                # Element has been removed
                indices_to_remove.append(i)
        # Remove no longer existing elements
        for i in reversed(indices_to_remove):
            del self._prop_val('elem_order')[i]
        # Add new elements
        for ref_id in ref_ids_to_add:
            self._prop_val('elem_order').append((ref_id, ref_elements[ref_id]))

        ret_group = Group(debug_info="Overlay")
        for (_, element) in self._prop_val('elem_order'):
            if element:
                ret_group.add(element)
        return ret_group
