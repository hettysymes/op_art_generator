import random

from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_implementations.shape import RectangleNode
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Colour, PT_List, PT_Bool, PT_Int, PT_Hidden, PropEntry, PortType
from ui.nodes.shape_datatypes import Group

DEF_RANDOM_LIST_SELECTOR_INFO = NodeInfo(
    description="Randomly select from a list.",
    port_defs={
        (PortIO.INPUT, 'list'): PortDef("List", PT_List()),
        (PortIO.OUTPUT, '_main'): PortDef("Random selection", PortType())
    },
    prop_entries={
        'use_seed': PropEntry(PT_Bool(),
                              display_name="Use random seed?",
                              description="If checked, use the provided seed for random selection. Random selections done with the same seed will always be the same.",
                              default_value=False),
        'user_seed': PropEntry(PT_Int(),
                               display_name="Random seed",
                               description="If random seed is used, use this as the random seed.",
                               default_value=42),
        '_actual_seed': PropEntry(PT_Hidden())
    }
)


class RandomListSelectorNode(UnitNode):
    NAME = "Random List Selector"
    DEFAULT_NODE_INFO = DEF_RANDOM_LIST_SELECTOR_INFO

    def compute(self):
        val_list = self._prop_val('list')
        if val_list is not None:
            if not val_list:
                raise NodeInputException("List must contain at least one item.", self.uid)
            if self._prop_val('use_seed'):
                rng = random.Random(self._prop_val('user_seed'))
            else:
                if not self._prop_val('_actual_seed'):
                    self.prop_vals['_actual_seed'] = random.random()
                rng = random.Random(self._prop_val('_actual_seed'))
            self.set_compute_result(rng.choice(val_list))

    def visualise(self):
        return None
        # random_item = self.get_compute_result()
        # if random_item:
        #     group = Group(debug_info="Random Colour Selector")
        #     group.add(RectangleNode.helper(colour))
        #     return group
        # return None
