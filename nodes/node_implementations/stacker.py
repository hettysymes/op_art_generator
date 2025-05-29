from typing import cast

from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus
from nodes.nodes import UnitNode
from nodes.prop_types import PT_Element, PT_List, PT_Enum, PT_Float, PT_ElementHolder
from nodes.prop_values import List, Float, Enum
from nodes.shape_datatypes import Group
from nodes.transforms import Translate, Scale

DEF_STACKER_NODE_INFO = PrivateNodeInfo(
    description="Stack multiple drawings together, either vertically or horizontally.",
    prop_defs={
        'elements': PropDef(
            prop_type=PT_List(PT_ElementHolder(), input_multiple=True),
            display_name="Drawings",
            description="Order of drawings in which to stack them. Drawings at the top of the list are drawn first (i.e. at the top for vertical stacking, and at the left for horizontal stacking).",
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            default_value=List(PT_ElementHolder())
        ),
        'layout_enum': PropDef(
            prop_type=PT_Enum(),
            display_name="Stack layout",
            description="Stacking of drawings can be done either top-to-bottom (vertical) or left-to-right (horizontal).",
            default_value=Enum([True, False], ["Vertical", "Horizontal"]),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN
        ),
        'wh_diff': PropDef(
            prop_type=PT_Float(),
            display_name="Overlap distance",
            description=(
                "Distance to place between stacked drawings, proportional to the height or width of one drawing "
                "(height for vertical stacking, width for horizontal stacking). E.g. if set to 0.5, the second drawing "
                "will be stacked halfway along the first drawing."
            ),
            default_value=Float(0)
        ),
        'shift': PropDef(
            prop_type=PT_Float(),
            display_name="Ascent/Right shift",
            description="Shift to the right or up (for horizontal and vertical stack respectively).",
            default_value=Float(0)
        ),
        '_main': PropDef(
            prop_type=PT_Element(),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Drawing",
            display_in_props=False
        )
    }
)


class StackerNode(UnitNode):
    NAME = "Stacker"
    DEFAULT_NODE_INFO = DEF_STACKER_NODE_INFO

    @staticmethod
    def helper(elements: List[PT_Element], wh_diff: float, vertical_layout: bool, shift: float):
        n = len(elements)
        size = n + wh_diff * (1 - n)
        group = Group(debug_info="Stacker")
        for i, e in enumerate(elements):
            if vertical_layout:
                transform = [Translate(0, -i * shift), Scale(1, 1 / size), Translate(0, i * (1 - wh_diff) / size)]
            else:
                transform = [Translate(0, -i * shift), Scale(1 / size, 1), Translate(i * (1 - wh_diff) / size, 0)]
            elem_cell = Group(transform, debug_info=f"Stack element {i}")
            elem_cell.add(e)
            group.add(elem_cell)
        return group

    def compute(self, props: ResolvedProps, *args):
        elem_entries: List[PT_ElementHolder] = props.get('elements')
        if not elem_entries:
            return {}
        main_group = StackerNode.helper(List(PT_Element(), [elem_entry.element for elem_entry in elem_entries]),
                                        props.get('wh_diff'),
                                        cast(Enum, props.get('layout_enum')).selected_option,
                                        props.get('shift'))
        return {'_main': main_group}
