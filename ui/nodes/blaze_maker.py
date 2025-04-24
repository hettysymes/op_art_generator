from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.elem_ref import ElemRef
from ui.nodes.multi_input_handler import handle_multi_inputs
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
        handle_multi_inputs(self.input_nodes, self.prop_vals['sample_order'])
        # Return element
        if self.input_nodes[0].compute():
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
