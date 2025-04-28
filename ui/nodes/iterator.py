import copy

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.grid import GridNode
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType, Node
from ui.nodes.shape_datatypes import Element
from ui.port_defs import PortDef, PortType, PT_ValueList, PT_Element, PT_ElementList

ITERATOR_NODE_INFO = UnitNodeInfo(
    name="Iterator",
    resizable=True,
    selectable=True,
    in_port_defs=[PortDef("Value list", PT_ValueList), PortDef("Shape", PT_Element)],
    out_port_defs=[PortDef("Iterator", PT_ElementList)],
    prop_type_list=PropTypeList(
        [
            PropType("prop_to_change", "prop_enum", default_value="",
                     description="Property of the input shape of which to modify using the value list.", display_name="Property to change")
        ]
    ),
    description="Given a list of values (a Colour List or the result of a Function Sampler), create multiple versions of a shape with a specified property modified with each of the values."
)


class IteratorNode(UnitNode):
    UNIT_NODE_INFO = ITERATOR_NODE_INFO

    def compute(self):
        samples = self.input_nodes[0].compute()
        shape_node: Node = self.input_nodes[1]
        element = shape_node.compute()
        if (samples is not None) and element:
            prop_key = self.prop_vals['prop_to_change']
            if prop_key and (prop_key in shape_node.prop_vals):
                ret = []
                for sample in samples:
                    node_copy = copy.deepcopy(shape_node)
                    node_copy.prop_vals[prop_key] = sample
                    ret.append(node_copy.compute())
                return ret

    def visualise(self, temp_dir, height, wh_ratio):
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
            return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (ret_element, None)).save()
