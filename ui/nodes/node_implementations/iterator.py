from ui.nodes.node_defs import NodeInfo
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Element, PT_List, PT_Scalar, PT_Enum, PropEntry

DEF_ITERATOR_INFO = NodeInfo(
    description="Given a list of values (a Colour List or the result of a Function Sampler), create multiple versions of a shape with a specified property modified with each of the values.",
    port_defs={
        (PortIO.INPUT, 'value_list'): PortDef("Value list", PT_List(PT_Scalar())),
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
        enum_type: PrT_Enum = self.node_info.prop_entries['prop_to_change'].prop_type
        elem_input = self._prop_val('element', get_refs=True)
        if not elem_input:
            enum_type.set_options([])
            return None
        ref_id, element = next(iter(elem_input.items()))
        node_id = self._port_ref('element', ref_id).node_id
        node = self.graph_querier.node(node_id)
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
        return node, prop_change_key, prop_types[prop_change_key]

    def _validate_values(self, prop_type):
        values_input = self._prop_val('value_list', get_refs=True)
        if not values_input:
            return None
        # TODO: for now assumes one input edge
        ref_id, values = next(iter(values_input.items()))
        port_type = self._port_ref('value_list', ref_id).port_def.port_type
        assert isinstance(port_type, PT_List)
        value_type = port_type.item_type
        # Check compatibility between value and property types
        assert isinstance(value_type, PT_Scalar)
        assert isinstance(prop_type, PT_Scalar)
        return value_type.is_compatible_with(prop_type)

    def compute(self, out_port_key='_main'):
        ret = self._update_prop_change_enum()
        if not ret:
            return None
        element_node, prop_change_key, prop_change_type = ret
        print(self._validate_values(prop_change_type))
        return None

    def visualise(self):
        self.compute()
        # elements = self.compute()
        # if elements:
        #     if self._prop_val('vis_layout') == "Vertical":
        #         # Draw in vertical grid
        #         grid = GridNode.helper(None, None, 1, len(elements))
        #     else:
        #         # Draw in Horizontal grid
        #         grid = GridNode.helper(None, None, len(elements), 1)
        #     return ShapeRepeaterNode.helper(grid, elements)
        return None
