import copy

from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_implementations.grid import GridNode
from ui.nodes.node_implementations.shape_repeater import ShapeRepeaterNode
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Element, PT_List, PT_Scalar, PT_Enum, PropEntry

DEF_ITERATOR_INFO = NodeInfo(
    description="Given a list of values (a Colour List or the result of a Function Sampler), create multiple versions of a shape with a specified property modified with each of the values.",
    port_defs={
        (PortIO.INPUT, 'value_list'): PortDef("Value list", PT_List(PT_Scalar(), input_multiple=False)),
        (PortIO.INPUT, 'element'): PortDef("Shape", PT_Element()),
        (PortIO.OUTPUT, '_main'): PortDef("Iterator", PT_List(PT_Element()))
    },
    prop_entries={
        'prop_to_change': PropEntry(PT_Enum(),
                                    display_name="Property to change",
                                    description="Property of the input shape of which to modify using the value list.",
                                    default_value=None),
        'vis_layout': PropEntry(PT_Enum(["Vertical", "Horizontal"]),
                                display_name="Visualisation layout",
                                description="Iterations can be visualised in either a vertical or horizontal layout. This only affects the visualisation for this node and not the output itself.",
                                default_value="Vertical")
    }
)


class IteratorNode(UnitNode):
    NAME = "Iterator"
    DEFAULT_NODE_INFO = DEF_ITERATOR_INFO

    def _update_prop_change_enum(self):
        enum_type: PT_Enum = self.node_info.prop_entries['prop_to_change'].prop_type
        elem_input = self._prop_val('element', get_refs=True)
        if not elem_input:
            enum_type.set_options()
            return None
        ref_id, element = elem_input
        port_ref = self._port_ref('element', ref_id)
        node = self.graph_querier.node(port_ref.node_id)
        options = []
        display_options = []
        prop_types = {}
        for prop_key, prop_entry in node.get_prop_entries().items():
            options.append(prop_key)
            display_options.append(prop_entry.display_name)
            prop_types[prop_key] = prop_entry.prop_type
        enum_type.set_options(options, display_options)
        # Update property to change if it is no longer an option
        if self._prop_val('prop_to_change') not in enum_type.get_options():
            self.set_property('prop_to_change', enum_type.get_options()[0])
        prop_change_key = self._prop_val('prop_to_change')
        return node, prop_change_key, prop_types[prop_change_key], port_ref.port_key

    def _validate_values(self, prop_type):
        values_input = self._prop_val('value_list', get_refs=True)
        if not values_input:
            return None
        ref_id, values = values_input
        port_type = self._port_ref('value_list', ref_id).port_def.port_type
        assert isinstance(port_type, PT_List)
        value_type = port_type.item_type
        # Check compatibility between value and property types
        assert isinstance(value_type, PT_Scalar)
        assert isinstance(prop_type, PT_Scalar)
        return values if value_type.is_compatible_with(prop_type) else None

    def compute(self):
        ret = self._update_prop_change_enum()
        if not ret:
            return
        element_node, prop_change_key, prop_change_type, src_port_key = ret
        values = self._validate_values(prop_change_type)
        if values is None:
            print("Values not compatible")
            return
        new_elements = []
        for value in values:
            new_element_node = copy.deepcopy(element_node)
            new_element_node.set_property(prop_change_key, value)
            new_element_node.compute()
            new_elements.append(new_element_node.get_compute_result(src_port_key))
        self.set_compute_result(new_elements)

    def visualise(self):
        elements = self.get_compute_result()
        if elements:
            if self._prop_val('vis_layout') == "Vertical":
                # Draw in vertical grid
                grid = GridNode.helper(None, None, 1, len(elements))
            else:
                # Draw in Horizontal grid
                grid = GridNode.helper(None, None, len(elements), 1)
            return ShapeRepeaterNode.helper(grid, elements)
        return None
