import copy

from ui.nodes.node_defs import NodeInfo, Node
from ui.nodes.node_implementations.grid import GridNode
from ui.nodes.node_implementations.shape_repeater import ShapeRepeaterNode
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Element, PT_List, PT_Scalar
from ui.nodes.prop_defs import PrT_String, PrT_Enum, PropEntry

DEF_ITERATOR_INFO = NodeInfo(
    description="Given a list of values (a Colour List or the result of a Function Sampler), create multiple versions of a shape with a specified property modified with each of the values.",
    port_defs={
        (PortIO.INPUT, 'value_list'): PortDef("Value list", PT_List(PT_Scalar())),
        (PortIO.INPUT, 'element'): PortDef("Shape", PT_Element()),
        (PortIO.OUTPUT, '_main'): PortDef("Iterator", PT_List(PT_Element()))
    },
    prop_entries={
        'prop_to_change': PropEntry(PrT_Enum(),
                                    display_name="Property to change",
                                    description="Property of the input shape of which to modify using the value list.",
                                    default_value=None),
        'vis_layout': PropEntry(PrT_Enum(["Vertical", "Horizontal"]),
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
            return
        ref_id, element = next(iter(elem_input.items()))
        node_id = self._port_ref('element', ref_id).node_id
        node = self.graph_querier.node(node_id)
        options = []
        display_options = []
        for prop_key, prop_entry in node.get_prop_entries().items():
            options.append(prop_key)
            display_options.append(prop_entry.display_name)
        enum_type.set_options(options, display_options)

    def compute(self, out_port_key='_main'):
        self._update_prop_change_enum()
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
