from ui_old.nodes.grid import GridNode
from ui_old.nodes.multi_input_handler import handle_multi_inputs
from ui_old.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui_old.nodes.shape_datatypes import Element, Group
from ui_old.nodes.shape_repeater import ShapeRepeaterNode
from ui_old.nodes.transforms import Scale, Translate
from ui_old.port_defs import PortDef, PT_Element, PT_Repeatable

STACKER_NODE_INFO = UnitNodeInfo(
    name="Stacker",
    in_port_defs=[
        PortDef("Input Drawings", PT_Repeatable, input_multiple=True, key_name='repeatables')
    ],
    out_port_defs=[PortDef("Drawing", PT_Element)],
    prop_type_list=PropTypeList([
        PropType("elem_order", "elem_table", default_value=[],
                 description="Order of drawings in which to stack them. Drawings at the top of the list are drawn first (i.e. at the top for vertical stacking, and at the left for horizontal stacking).",
                 display_name="Drawing order"),
        PropType("stack_layout", "enum", default_value="Vertical", options=["Vertical", "Horizontal"],
                 description="Stacking of drawings can be done either top-to-bottom (vertical) or left-to-right (horizontal)",
                 display_name="Stack layout"),
        PropType("wh_diff", "float", default_value=0.4, min_value=0.1,
                 description="Distance to place between stacked drawings, proportional to the height or width of one drawing (height for vertical stacking, width for horizontal stacking). E.g. if set to 0.5, the second drawing will be stacked halfway along the first drawing.",
                 display_name="Height/width distance")
    ]),
    description="Stack multiple drawings together, either vertically or horizontally."
)


class StackerNode(UnitNode):
    UNIT_NODE_INFO = STACKER_NODE_INFO

    @staticmethod
    def helper(elements, wh_diff, vertical_layout):
        n = len(elements)
        size = n + wh_diff*(1-n)
        group = Group(debug_info="stacker")
        for i, e in enumerate(elements):
            if vertical_layout:
                transform = [Scale(1, 1/size), Translate(0, i*(1 - wh_diff)/size)]
            else:
                transform = [Scale(1/size, 1), Translate(i*(1 - wh_diff)/size, 0)]
            elem_cell = Group(transform, debug_info=f"Stack element {i}")
            elem_cell.add(e)
            group.add(elem_cell)
        return group

    def compute(self):
        handle_multi_inputs(self.get_input_node('repeatables'), self.prop_vals['elem_order'])
        elements = []
        for elem_ref in self.get_prop_val('elem_order'):
            ret_elements = elem_ref.compute()
            if isinstance(ret_elements, Element):
                ret_elements = [ret_elements]
            elements += ret_elements
        if elements:
            return StackerNode.helper(elements, self.get_prop_val('wh_diff'),
                                      self.get_prop_val('stack_layout') == 'Vertical')
        return None
