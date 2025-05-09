from ui.nodes.node_defs import NodeInfo, PropEntry, PropType
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortDef, PT_Element, PT_Repeatable, PortIO
from ui.nodes.shape_datatypes import Group, Element
from ui.nodes.transforms import Translate, Scale

DEF_STACKER_NODE_INFO = NodeInfo(
    description="Stack multiple drawings together, either vertically or horizontally.",
    port_defs={
        (PortIO.INPUT, 'repeatables'): PortDef("Input Drawings", PT_Repeatable),
        (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Element)
    },
    prop_entries={
        'elem_order': PropEntry(PropType.ELEM_TABLE,
                                display_name="Drawing order",
                                description="Order of drawings in which to stack them. Drawings at the top of the list are drawn first (i.e. at the top for vertical stacking, and at the left for horizontal stacking).",
                                default_value=[]),
        'stack_layout': PropEntry(PropType.ENUM,
                                  display_name="Stack layout",
                                  description="Stacking of drawings can be done either top-to-bottom (vertical) or left-to-right (horizontal)",
                                  default_value="Vertical",
                                  options=["Vertical", "Horizontal"]),
        'wh_diff': PropEntry(PropType.FLOAT,
                             display_name="Height/width distance",
                             description="Distance to place between stacked drawings, proportional to the height or width of one drawing (height for vertical stacking, width for horizontal stacking). E.g. if set to 0.5, the second drawing will be stacked halfway along the first drawing.",
                             default_value=0.4, min_value=0.1)
    }
)


class StackerNode(UnitNode):
    NAME = "Stacker"
    DEFAULT_NODE_INFO = DEF_STACKER_NODE_INFO

    @staticmethod
    def helper(elements, wh_diff, vertical_layout):
        n = len(elements)
        size = n + wh_diff * (1 - n)
        group = Group(debug_info="stacker")
        for i, e in enumerate(elements):
            if vertical_layout:
                transform = [Scale(1, 1 / size), Translate(0, i * (1 - wh_diff) / size)]
            else:
                transform = [Scale(1 / size, 1), Translate(i * (1 - wh_diff) / size, 0)]
            elem_cell = Group(transform, debug_info=f"Stack element {i}")
            elem_cell.add(e)
            group.add(elem_cell)
        return group

    def compute(self, out_port_key='_main'):
        # handle_multi_inputs(self.get_input_node('repeatables'), self.prop_vals['elem_order'])
        elements = []
        for elem_ref in self._prop_val('elem_order'):
            ret_elements = elem_ref.compute()
            if isinstance(ret_elements, Element):
                ret_elements = [ret_elements]
            elements += ret_elements
        if elements:
            return StackerNode.helper(elements, self._prop_val('wh_diff'),
                                      self._prop_val('stack_layout') == 'Vertical')
        return None
