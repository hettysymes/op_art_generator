import random

from ui_old.nodes.node_input_exception import NodeInputException
from ui_old.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui_old.nodes.shape import RectangleNode
from ui_old.nodes.shape_datatypes import Group
from ui_old.port_defs import PortDef, PT_ColourList, PT_Colour

RANDOM_COLOUR_SELECTOR_NODE_INFO = UnitNodeInfo(
    name="Random Colour Selector",
    selectable=False,
    in_port_defs=[PortDef("Colour list", PT_ColourList, key_name='colour_list')],
    out_port_defs=[PortDef("Random colour", PT_Colour)],
    prop_type_list=PropTypeList(
        [
            PropType("use_seed", "bool",
                     description="If checked, use the provided seed for random selection. Random selections done with the same seed will always be the same.",
                     display_name="Use random seed?", auto_format=False),
            PropType("user_seed", "int", default_value=42,
                     description="If random seed is used, use this as the random seed.", display_name="Random seed"),
            PropType("_actual_seed", "hidden")
        ]
    ),
    description="Randomly select a colour from a colour list."
)


class RandomColourSelectorNode(UnitNode):
    UNIT_NODE_INFO = RANDOM_COLOUR_SELECTOR_NODE_INFO

    def compute(self):
        colours = self.get_input_node('colour_list').compute()
        if colours is not None:
            if not colours:
                raise NodeInputException("At least one input colour is required.", self.node_id)
            if self.get_prop_val('use_seed'):
                rng = random.Random(self.get_prop_val('user_seed'))
            else:
                if not self.get_prop_val('_actual_seed'):
                    self.prop_vals['_actual_seed'] = random.random()
                rng = random.Random(self.get_prop_val('_actual_seed'))
            return rng.choice(colours)
        return None

    def visualise(self):
        colour = self.compute()
        if colour:
            group = Group(debug_info="Random Colour Selector")
            group.add(RectangleNode.helper(colour))
            return group
        return None
