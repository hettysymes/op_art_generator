from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.elem_ref import ElemRef
from ui.nodes.ellipse_sampler import EllipseSamplerNode
from ui.nodes.multi_input_handler import handle_multi_inputs
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape_datatypes import Element, PolyLine
from ui.port_defs import PortType, PortDef

BLAZE_MAKER_NODE_INFO = UnitNodeInfo(
    name="Blaze Maker",
    resizable=True,
    selectable=True,
    in_port_defs=[
        PortDef("Input Ellipses", PortType.ELEMENT, input_multiple=True)
    ],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList([
        PropType("num_samples", "int", default_value=72,
                 description="", min_value=1, display_name="number of samples"),
        PropType("angle_diff", "float", default_value=20,
                         description="", min_value=-360, max_value=360, display_name="angle difference"),
        PropType("ellipse_order", "elem_table", default_value=[],
                             description="", display_name="ellipse order")
    ])
)


class BlazeMakerNode(UnitNode):
    UNIT_NODE_INFO = BLAZE_MAKER_NODE_INFO

    def compute(self):
        handle_multi_inputs(self.input_nodes, self.prop_vals['ellipse_order'])
        # Return element
        if self.input_nodes[0].compute():
            ret_elem = Element()
            ellipse_elems = [elem_ref.compute() for elem_ref in self.prop_vals['ellipse_order']]
            start_angle = 0
            angle_diff = self.prop_vals['angle_diff']
            samples_list = []
            for elem in ellipse_elems:
                start_angle += angle_diff
                angle_diff *= -1
                samples_list.append(EllipseSamplerNode.helper(elem, start_angle, self.prop_vals['num_samples']))
            lines = [[] for _ in range(self.prop_vals['num_samples'])]
            for samples in samples_list:
                for i, sample in enumerate(samples):
                    lines[i].append(sample)
            for line in lines:
                ret_elem.add(PolyLine(line, 'black', 1))
            return ret_elem

    def visualise(self, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (element, None)).save()
