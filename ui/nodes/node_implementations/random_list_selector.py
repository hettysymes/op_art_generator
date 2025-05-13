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
        (PortIO.INPUT, 'list'): PortDef("List", PT_List(input_multiple=False)),
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
        val_list = self._prop_val('list', get_refs=True)
        if not val_list:
            # Update output port type
            self.get_port_defs()[(PortIO.OUTPUT, '_main')].port_type = PortType()
            return
        ref_id, values = val_list
        # Update output port type
        list_port_type = self._port_ref('list', ref_id).port_def.port_type
        self.get_port_defs()[(PortIO.OUTPUT, '_main')].port_type = list_port_type.item_type
        if not values:
            raise NodeInputException("List must contain at least one item.", self.uid)
        if self._prop_val('use_seed'):
            rng = random.Random(self._prop_val('user_seed'))
        else:
            if self._prop_val('_actual_seed') is None:
                self.prop_vals['_actual_seed'] = random.random()
            rng = random.Random(self._prop_val('_actual_seed'))
        self.set_compute_result(rng.choice(values))

    def randomise(self):
        self.set_property('_actual_seed', None)

    @property
    def randomisable(self):
        return True
