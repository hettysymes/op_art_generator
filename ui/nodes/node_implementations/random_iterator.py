import copy
import random

from ui.nodes.node_defs import NodeInfo, PortRef
from ui.nodes.node_implementations.shape import RectangleNode
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Colour, PT_List, PT_Bool, PT_Int, PT_Hidden, PropEntry, PortType, \
    get_most_general_type, PT_Element
from ui.nodes.shape_datatypes import Group

DEF_RANDOM_ITERATOR_INFO = NodeInfo(
    description="Create a specified number of random iterations, outputting a drawing.",
    port_defs={
        (PortIO.INPUT, 'input'): PortDef("Random node", PT_List(input_multiple=False)),
        (PortIO.OUTPUT, '_main'): PortDef("Random iterations", PortType())
    },
    prop_entries={
        'num_iterations': PropEntry(PT_Int(min_value=1),
                                    display_name="Number of iterations",
                                    description="Number of random iterations of a node output to create, at least 1.",
                                    default_value=3),
        '_actual_seed': PropEntry(PT_Hidden())
    }
)


class RandomIteratorNode(UnitNode):
    NAME = "Random Iterator"
    DEFAULT_NODE_INFO = DEF_RANDOM_ITERATOR_INFO

    def compute(self):
        id_elem = self._prop_val('input', get_refs=True)
        if not id_elem:
            # Reset output port type
            self.get_port_defs()[(PortIO.OUTPUT, '_main')].port_type = PortType()
            return
        ref_id, input_value = id_elem
        port_ref: PortRef = self._port_ref('input', ref_id)
        src_node = self.graph_querier.node(port_ref.node_id)
        num_iterations = self._prop_val('num_iterations')

        # Set output port type to be list of input type
        self.get_port_defs()[(PortIO.OUTPUT, '_main')].port_type = PT_List(port_ref.port_def.port_type)

        # If input node is not randomisable, just return the input the given number of times
        if not src_node.randomisable:
            self.set_compute_result([input_value for _ in range(num_iterations)])
            return

        # Get random seeds
        if self.get_actual_seed() is None:
            self.set_actual_seed(random.random())
        rng = random.Random(self.get_actual_seed())
        seeds = [rng.random() for _ in range(num_iterations)]

        # Calculate and set random compute result
        outputs = []
        for seed in seeds:
            random_node = copy.deepcopy(src_node)
            random_node.set_actual_seed(seed)
            random_node.clear_compute_results()
            random_node.final_compute()
            outputs.append(random_node.get_compute_result(port_ref.port_key))
        self.set_compute_result(outputs)

    # Functions needed for randomisable node # TODO make into interface

    def randomise(self):
        self.set_property('_actual_seed', None)

    def get_actual_seed(self):
        return self._prop_val('_actual_seed')

    def set_actual_seed(self, value):
        self.set_property('_actual_seed', value)

    @property
    def randomisable(self):
        return True
