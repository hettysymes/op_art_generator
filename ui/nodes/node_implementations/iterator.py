import copy

from ui.nodes.node_defs import NodeInfo, PropType, PropEntry, Node
from ui.nodes.node_implementations.grid import GridNode
from ui.nodes.node_implementations.shape_repeater import ShapeRepeaterNode
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Element, PT_List, PT_Scalar

DEF_ITERATOR_INFO = NodeInfo(
    description="Given a list of values (a Colour List or the result of a Function Sampler), create multiple versions of a shape with a specified property modified with each of the values.",
    port_defs={
        (PortIO.INPUT, 'value_list'): PortDef("Value list", PT_List(PT_Scalar())),
        (PortIO.INPUT, 'element'): PortDef("Shape", PT_Element()),
        (PortIO.OUTPUT, '_main'): PortDef("Iterator", PT_List(PT_Element()))
    },
    prop_entries={
        'prop_to_change': PropEntry(PropType.STRING,
                                    display_name="Property to change",
                                    description="Property of the input shape of which to modify using the value list.",
                                    default_value=""),
        'vis_layout': PropEntry(PropType.ENUM,
                                display_name="Visualisation layout",
                                description="Iterations can be visualised in either a vertical or horizontal layout. This only affects the visualisation for this node and not the output itself.",
                                default_value="Vertical",
                                options=["Vertical", "Horizontal"])
    }
)


def normalize_type(t):
    import numpy as np
    if isinstance(t, np.generic):
        t = t.item()
    return type(t)


class IteratorNode(UnitNode):
    NAME = "Iterator"
    DEFAULT_NODE_INFO = DEF_ITERATOR_INFO

    def compute(self, out_port_key='_main'):
        samples = self._prop_val('value_list')
        shape_node: Node = self._prop_val('element')
        element = shape_node.compute()
        if (samples is not None) and element:
            prop_key = self._prop_val('prop_to_change')
            if prop_key and (prop_key in shape_node.prop_vals):
                ret = []
                for sample in samples:
                    node_copy = copy.deepcopy(shape_node)
                    sample_type = normalize_type(sample)
                    if sample_type != normalize_type(shape_node._prop_val(prop_key)):
                        raise NodeInputException(
                            "Type of value list samples are not compatible with the selected property.", self.uid)
                    # Check the sample is within the min and max range for floats and ints
                    if sample_type in (int, float):
                        # TODO: fix
                        matching_prop = next((p for p in shape_node.prop_type_list() if p.key_name == prop_key), None)
                        if ((matching_prop.min_value is not None) and sample < matching_prop.min_value) or (
                                (matching_prop.max_value is not None) and sample > matching_prop.max_value):
                            raise NodeInputException(
                                "Value list includes samples not in allowed in the property range.",
                                self.uid)
                    node_copy.prop_vals[prop_key] = sample
                    try:
                        compute_res = node_copy.compute()
                    except NodeInputException as e:
                        raise NodeInputException(e.message, self.uid)
                    ret.append(compute_res)
                return ret
            return None
        return None

    def visualise(self):
        elements = self.compute()
        if elements:
            if self._prop_val('vis_layout') == "Vertical":
                # Draw in vertical grid
                grid = GridNode.helper(None, None, 1, len(elements))
            else:
                # Draw in Horizontal grid
                grid = GridNode.helper(None, None, len(elements), 1)
            return ShapeRepeaterNode.helper(grid, elements)
        return None
