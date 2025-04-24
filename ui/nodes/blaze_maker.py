from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.elem_ref import ElemRef
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape_datatypes import Element, PolyLine
from ui.port_defs import PortType, PortDef

BLAZE_MAKER_NODE_INFO = UnitNodeInfo(
    name="Blaze Maker",
    resizable=True,
    selectable=True,
    in_port_defs=[
        PortDef("Input Samples", PortType.VALUE_LIST, input_multiple=True)
    ],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList([
        PropType("sample_order", "elem_table", default_value=[],
                             description="", display_name="sample order")
    ])
)


class BlazeMakerNode(UnitNode):
    UNIT_NODE_INFO = BLAZE_MAKER_NODE_INFO

    def compute(self):
        sample_nodes = self.input_nodes
        sample_node_ids = []
        if sample_nodes[0].compute():
            sample_node_ids = [sn.node_id for sn in sample_nodes]
        indices_to_remove = []
        for i, elem_ref in enumerate(self.prop_vals['sample_order']):
            if elem_ref.node_id in sample_node_ids:
                # Element already exists - mark as not to add
                index = sample_node_ids.index(elem_ref.node_id)
                sample_node_ids[index] = None
            else:
                # Element has been removed
                indices_to_remove.append(i)
        # Remove no longer existing elements
        for i in reversed(indices_to_remove):
            del self.prop_vals['sample_order'][i]
        # Add new elements
        for i, sn_id in enumerate(sample_node_ids):
            if sn_id is not None:
                self.prop_vals['sample_order'].append(ElemRef(sample_nodes[i]))
        # Return element
        if sample_nodes[0].compute():
            ret_elem = Element()
            samples_list = [elem_ref.compute() for elem_ref in self.prop_vals['sample_order']]
            num_samples_each = len(samples_list[0])
            lines = [[] for _ in range(num_samples_each)]
            for samples in samples_list:
                assert len(samples) == num_samples_each # TODO: add error message
                for i, sample in enumerate(samples):
                    lines[i].append(sample)
            for line in lines:
                ret_elem.add(PolyLine(line, 'black', 1))
            return ret_elem

    def visualise(self, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (element, None)).save()
