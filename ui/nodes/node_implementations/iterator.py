import copy
from typing import Optional

from ui.id_datatypes import PropKey
from ui.node_graph import RefId
from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps, ResolvedRefs, RefQuerier, Node
from ui.nodes.nodes import UnitNode
from ui.nodes.prop_defs import PropDef, PT_List, PT_Element, PT_Enum, PortStatus, String, List, Bool

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
        'prop_to_change': PropDef(
            prop_type=PT_Enum(),
            display_name="Property to change",
            description="Property of the input shape of which to modify using the value list.",
            default_value=None,
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN
        ),
        'vertical_layout': PropDef(
            prop_type=PT_Enum([True, False], ["Vertical", "Horizontal"]),
            display_name="Visualisation layout",
            description="Iterations can be visualised in either a vertical or horizontal layout. This only affects the visualisation for this node and not the output itself.",
            default_value=Bool(True),
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
    NAME = "Iterator"
    DEFAULT_NODE_INFO = DEF_ITERATOR_INFO

    def _update_prop_change_enum(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier) -> bool:
        enum_type: PT_Enum = self.prop_defs['prop_to_change'].prop_type
        elem_input = props.get('element')
        if elem_input is None:
            enum_type.set_options()
            return False
        node_info = ref_querier.node_info(refs.get('element'))
        options = []
        display_options = []
        prop_types = {}
        for prop_key, prop_def in node_info.prop_defs.items():
            options.append(prop_key)
            display_options.append(prop_def.display_name)
            prop_types[prop_key] = prop_def.prop_type
        enum_type.set_options(options, display_options)
        # Update property to change if it is no longer an option
        if props.get('prop_to_change') not in enum_type.options:
            self.internal_props['prop_to_change'] = String(enum_type.options[0])
        return True

    # def _validate_values(self, prop_type):
    #     values_input = self._prop_val('value_list', get_refs=True)
    #     if not values_input:
    #         return None
    #     ref_id, values = values_input
    #     port_type = self._port_ref('value_list', ref_id).port_def.port_type
    #     assert isinstance(port_type, PT_List)
    #     value_type = port_type.item_type
    #     # Check compatibility between value and property types
    #     assert isinstance(value_type, PT_Scalar)
    #     assert isinstance(prop_type, PT_Scalar)
    #     return values if value_type.is_compatible_with(prop_type) else None

    def compute(self, props: ResolvedProps, refs: ResolvedRefs, ref_querier: RefQuerier):
        if not self._update_prop_change_enum(props, refs, ref_querier):
            return {}

        # values = self._validate_values(prop_change_type)
        # if values is None:
        #     print("Values not compatible")
        #     return
        prop_change_key: PropKey = props.get('prop_to_change')
        elem_ref: RefId = refs.get('element')
        src_port_key: PropKey = ref_querier.port(elem_ref).key
        element_node: Node = ref_querier.node_copy(elem_ref)
        values: List = props.get('value_list')

        new_elements = List(PT_Element(), vertical_layout=props.get('vertical_layout'))
        for value in values:
            in_props, in_refs, in_querier = ref_querier.get_compute_inputs(elem_ref)
            in_props[prop_change_key] = value
            elem = element_node.final_compute(in_props, in_refs, in_querier)[src_port_key]
            new_elements.append(elem)
        return {'_main': new_elements}
