from typing import Optional, cast

from ui.id_datatypes import PropKey
from ui.node_graph import RefId
from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps, ResolvedRefs, RefQuerier, Node
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode
from ui.nodes.prop_defs import PropDef, PT_List, PT_Element, Enum, PortStatus, List, PropType, PT_Enum

DEF_ITERATOR_INFO = PrivateNodeInfo(
    description="Given a list of values (a Colour List or the result of a Function Sampler), create multiple versions of a shape with a specified property modified with each of the values.",
    prop_defs={
        'value_list': PropDef(
            prop_type=PT_List(input_multiple=False),
            display_name="Value list",
            input_port_status=PortStatus.COMPULSORY,
            default_value=List()
        ),
        'element': PropDef(
            prop_type=PT_Element(),
            display_name="Shape",
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
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Iterator",
            display_in_props=False
        )
    }
)


class IteratorNode(UnitNode):
    NAME = "Property Iterator"
    DEFAULT_NODE_INFO = DEF_ITERATOR_INFO

    def _update_prop_change_enum(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier) -> bool:
        enum: Enum = props.get('prop_enum')
        elem_input: Optional[PT_Element] = props.get('element')
        if elem_input is None:
            enum.set_options()
            return False
        # Update enum
        node_info = ref_querier.node_info(refs.get('element'))
        options = []
        display_options = []
        prop_types = {}
        for prop_key, prop_def in node_info.prop_defs.items():
            if cast(PropDef, prop_def).display_in_props:
                options.append(prop_key)
                display_options.append(prop_def.display_name)
                prop_types[prop_key] = prop_def.prop_type
        enum.set_options(options, display_options)
        return True

    def compute(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier):
        if not self._update_prop_change_enum(props, refs, ref_querier):
            return {}

        prop_change_key: PropKey = cast(Enum, props.get('prop_enum')).selected_option
        assert prop_change_key is not None
        values: List = props.get('value_list')
        elem_ref: RefId = refs.get('element')
        element_node: Node = ref_querier.node_copy(elem_ref)
        prop_type: PropType = element_node.prop_defs[prop_change_key].prop_type

        if not values.item_type.is_compatible_with(prop_type):
            raise NodeInputException(
                f"Values of type {values.item_type} is not compatible with expected input type {prop_type}.")

        src_port_key: PropKey = ref_querier.port(elem_ref).key
        new_elements = List(PT_Element(), vertical_layout=cast(Enum, props.get('layout_enum')).selected_option)
        for value in values:
            in_props, in_refs, in_querier = ref_querier.get_compute_inputs(elem_ref)
            in_props[prop_change_key] = value
            elem = element_node.final_compute(in_props, in_refs, in_querier)[src_port_key]
            new_elements.append(elem)
        return {'_main': new_elements}
