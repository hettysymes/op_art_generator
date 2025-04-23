import copy

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.grid import GridNode
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType, Node
from ui.nodes.shape_datatypes import Element
from ui.port_defs import PortDef, PortType

ITERATOR_NODE_INFO = UnitNodeInfo(
    name="Iterator",
    resizable=True,
    selectable=True,
    in_port_defs=[PortDef("Value list", PortType.VALUE_LIST), PortDef("Shape", PortType.ELEMENT)],
    out_port_defs=[PortDef("Iterator", PortType.ELEMENT)],
    prop_type_list=PropTypeList(
        [
            PropType("prop_to_change", "string", default_value="",
                     description="", display_name="property to change")
        ]
    )
)


class IteratorNode(UnitNode):
    UNIT_NODE_INFO = ITERATOR_NODE_INFO

    def compute(self):
        samples = self.input_nodes[0].compute()
        shape_node: Node = self.input_nodes[1]
        element = shape_node.compute()
        if (samples is not None) and element:
            prop_key = self.prop_vals['prop_to_change']
            if prop_key in shape_node.prop_vals:
                ret = []
                for sample in samples:
                    node_copy = copy.deepcopy(shape_node)
                    node_copy.prop_vals[prop_key] = sample
                    ret.append(node_copy.compute())
                return ret

    def visualise(self, height, wh_ratio):
        elements = self.compute()
        if elements:
            # Draw in vertical grid
            v_line_xs, h_line_ys = GridNode.helper(None, None, 1, len(elements))
            ret_element = Element()
            elem_index = 0
            for i in range(1, len(v_line_xs)):
                for j in range(1, len(h_line_ys)):
                    x1 = v_line_xs[i - 1]
                    x2 = v_line_xs[i]
                    y1 = h_line_ys[j - 1]
                    y2 = h_line_ys[j]
                    ret_element.add(elements[elem_index][0].scale(x2 - x1, y2 - y1).translate(x1, y1))
                    elem_index += 1
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (ret_element, None)).save()
