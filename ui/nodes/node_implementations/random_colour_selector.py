import random

from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_implementations.shape import RectangleNode
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Colour, PT_List
from ui.nodes.prop_defs import PropEntry, PrT_Bool, PrT_Int, PrT_Hidden
from ui.nodes.shape_datatypes import Group

DEF_RANDOM_COLOUR_SELECTOR_INFO = NodeInfo(
    description="Randomly select a colour from a colour list.",
    port_defs={
        (PortIO.INPUT, 'colour_list'): PortDef("Colour list", PT_List(PT_Colour())),
        (PortIO.OUTPUT, '_main'): PortDef("Random colour", PT_Colour())
    },
    prop_entries={
        'use_seed': PropEntry(PrT_Bool(),
                              display_name="Use random seed?",
                              description="If checked, use the provided seed for random selection. Random selections done with the same seed will always be the same.",
                              default_value=False),
        'user_seed': PropEntry(PrT_Int(),
                               display_name="Random seed",
                               description="If random seed is used, use this as the random seed.",
                               default_value=42),
        '_actual_seed': PropEntry(PrT_Hidden())
    }
)


class RandomColourSelectorNode(UnitNode):
    NAME = "Random Colour Selector"
    DEFAULT_NODE_INFO = DEF_RANDOM_COLOUR_SELECTOR_INFO

    def compute(self, out_port_key='_main'):
        colours = self._prop_val('colour_list')
        if colours is not None:
            if not colours:
                raise NodeInputException("At least one input colour is required.", self.uid)
            if self._prop_val('use_seed'):
                rng = random.Random(self._prop_val('user_seed'))
            else:
                if not self._prop_val('_actual_seed'):
                    self.prop_vals['_actual_seed'] = random.random()
                rng = random.Random(self._prop_val('_actual_seed'))
            return rng.choice(colours)
        return None

    def visualise(self):
        colour = self.compute()
        if colour:
            group = Group(debug_info="Random Colour Selector")
            group.add(RectangleNode.helper(colour))
            return group
        return None
