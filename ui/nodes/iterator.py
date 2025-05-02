import copy

from ui.nodes.drawers.group_drawer import GroupDrawer
from ui.nodes.grid import GridNode
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType, Node
from ui.nodes.shape_repeater import ShapeRepeaterNode
from ui.port_defs import PortDef, PT_ValueList, PT_Element, PT_ElementList

ITERATOR_NODE_INFO = UnitNodeInfo(
    name="Iterator",
    in_port_defs=[PortDef("Value list", PT_ValueList, key_name='value_list'),
                  PortDef("Shape", PT_Element, key_name='element')],
    out_port_defs=[PortDef("Iterator", PT_ElementList)],
    prop_type_list=PropTypeList(
        [
            PropType("prop_to_change", "prop_enum", default_value="",
                     description="Property of the input shape of which to modify using the value list.",
                     display_name="Property to change"),
            PropType("vis_layout", "enum", default_value="Vertical", options=["Vertical", "Horizontal"],
                     description="Iterations can be visualised in either a vertical or horizontal layout. This only affects the visualisation for this node and not the output itself.",
                     display_name="Visualisation layout")
        ]
    ),
    description="Given a list of values (a Colour List or the result of a Function Sampler), create multiple versions of a shape with a specified property modified with each of the values."
)


def normalize_type(t):
    import numpy as np
    if isinstance(t, np.generic):
        t = t.item()
    return type(t)


class IteratorNode(UnitNode):
    UNIT_NODE_INFO = ITERATOR_NODE_INFO

    def compute(self):
        samples = self.get_input_node('value_list').compute()
        shape_node: Node = self.get_input_node('element')
        element = shape_node.compute()
        if (samples is not None) and element:
            prop_key = self.get_prop_val('prop_to_change')
            if prop_key and (prop_key in shape_node.prop_vals):
                ret = []
                for sample in samples:
                    node_copy = copy.deepcopy(shape_node)
                    sample_type = normalize_type(sample)
                    if sample_type != normalize_type(shape_node.get_prop_val(prop_key)):
                        raise NodeInputException(
                            "Type of value list samples are not compatible with the selected property.", self.node_id)
                    # Check the sample is within the min and max range for floats and ints
                    if sample_type in (int, float):
                        matching_prop = next((p for p in shape_node.prop_type_list() if p.key_name == prop_key), None)
                        if ((matching_prop.min_value is not None) and sample < matching_prop.min_value) or (
                                (matching_prop.max_value is not None) and sample > matching_prop.max_value):
                            raise NodeInputException(
                                "Value list includes samples not in allowed in the property range.",
                                self.node_id)
                    node_copy.prop_vals[prop_key] = sample
                    try:
                        compute_res = node_copy.compute()
                    except NodeInputException as e:
                        raise NodeInputException(e.message, self.node_id)
                    ret.append(compute_res)
                return ret
            return None
        return None

    def visualise(self):
        elements = self.compute()
        if elements:
            if self.get_prop_val('vis_layout') == "Vertical":
                # Draw in vertical grid
                grid = GridNode.helper(None, None, 1, len(elements))
            else:
                # Draw in Horizontal grid
                grid = GridNode.helper(None, None, len(elements), 1)
            return ShapeRepeaterNode.helper(grid, elements)
        return None
