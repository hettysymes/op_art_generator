from typing import Optional, cast

from sympy.integrals.risch import NonElementaryIntegral

from id_datatypes import PropKey
from node_graph import RefId
from nodes.node_defs import PrivateNodeInfo, ResolvedProps, ResolvedRefs, RefQuerier, Node, PropDef, PortStatus, \
    NodeCategory, DisplayStatus
from nodes.node_input_exception import NodeInputException
from nodes.nodes import UnitNode
from nodes.prop_types import PT_List, PropType, PT_Enum
from nodes.prop_values import List, Enum

DEF_ITERATOR_INFO = PrivateNodeInfo(
    description="Given a list of values (a Colour List or the result of a Function Sampler), create multiple versions of a shape with a specified property modified with each of the values.",
    prop_defs={
        'value_list': PropDef(
            prop_type=PT_List(input_multiple=False),
            display_name="Value list",
            input_port_status=PortStatus.COMPULSORY,
            default_value=List()
        ),
        'node_input': PropDef(
            prop_type=PropType(),
            display_name="Node",
            input_port_status=PortStatus.COMPULSORY
        ),
        'prop_enum': PropDef(
            prop_type=PT_Enum(),
            display_name="Property to change",
            description="Property of the input shape of which to modify using the value list.",
            default_value=Enum(),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN
        ),
        'layout_enum': PropDef(
            prop_type=PT_Enum(),
            display_name="Visualisation layout",
            description="Iterations can be visualised in either a vertical or horizontal layout. This only affects the visualisation for this node and not the output itself.",
            default_value=Enum([True, False], ["Vertical", "Horizontal"]),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN
        ),
        '_main': PropDef(
            prop_type=PT_List(),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Iterations",
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class IteratorNode(UnitNode):
    NAME = "Property Iterator"
    NODE_CATEGORY = NodeCategory.PROPERTY_MODIFIER
    DEFAULT_NODE_INFO = DEF_ITERATOR_INFO

    def _update_prop_change_enum(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier) -> bool:
        enum: Enum = props.get('prop_enum')
        node_input = props.get('node_input')
        if node_input is None:
            enum.set_options()
            return False
        # Update enum
        node_info = ref_querier.node_info(refs.get('node_input'))
        options = []
        display_options = []
        prop_types = {}
        for prop_key, prop_def in node_info.prop_defs.items():
            if cast(PropDef, prop_def).display_status != DisplayStatus.NO_DISPLAY:
                options.append(prop_key)
                display_options.append(prop_def.display_name)
                prop_types[prop_key] = prop_def.prop_type
        enum.set_options(options, display_options)
        return True

    def compute(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier):
        if not self._update_prop_change_enum(props, refs, ref_querier):
            return {}

        prop_change_key: PropKey = cast(Enum, props.get('prop_enum')).selected_option
        if prop_change_key is None:
            return {}
        values: List = props.get('value_list')
        node_input = props.get('node_input')
        node_ref: RefId = refs.get('node_input')
        actual_node: Node = ref_querier.node_copy(node_ref)
        prop_type: PropType = actual_node.prop_defs[prop_change_key].prop_type

        if not values.item_type.is_compatible_with(prop_type):
            raise NodeInputException(
                f"Values of type {values.item_type} is not compatible with expected input type {prop_type}.")

        src_port_key: PropKey = ref_querier.port(node_ref).key
        iter_outputs = List(node_input.type, vertical_layout=cast(Enum, props.get('layout_enum')).selected_option)
        for value in values:
            in_props, in_refs, in_querier = ref_querier.get_compute_inputs(node_ref)
            in_props[prop_change_key] = value
            iteration_item = actual_node.final_compute(in_props, in_refs, in_querier)[src_port_key]
            iter_outputs.append(iteration_item)
        return {'_main': iter_outputs}
