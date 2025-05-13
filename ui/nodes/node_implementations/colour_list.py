from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_implementations.grid import GridNode
from ui.nodes.node_implementations.port_ref_table_handler import handle_port_ref_table
from ui.nodes.node_implementations.shape import RectangleNode
from ui.nodes.node_implementations.shape_repeater import ShapeRepeaterNode
from ui.nodes.nodes import UnitNode, SelectableNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Colour, PT_List, PT_ColourRefTable, PropEntry

DEF_COLOUR_LIST_INFO = NodeInfo(
    description="Define a list of colours. This can be provided as input to an Iterator or a Colour Filler.",
    port_defs={
        (PortIO.INPUT, 'import_colours'): PortDef("Import Colours", PT_List(PT_Colour())),
        (PortIO.OUTPUT, '_main'): PortDef("Colours", PT_List(PT_Colour()))
    },
    prop_entries={
        'colour_order': PropEntry(PT_ColourRefTable('import_colours'),
                                  display_name="Colours",
                                  description="Colours to populate the colour list.",
                                  default_value=[(0, 0, 0, 255), (255, 0, 0, 255), (0, 255, 0, 255)])
    }
)


class ColourListNode(SelectableNode):
    NAME = "Colour List"
    DEFAULT_NODE_INFO = DEF_COLOUR_LIST_INFO

    def compute(self):
        ref_colours = self._prop_val('import_colours', get_refs=True)
        colours = handle_port_ref_table(ref_colours, self._prop_val('colour_order'))
        print(colours)
        self.set_compute_result(colours)
        for port_id in self.extracted_port_ids:
            _, port_key = port_id
            _, i = port_key.split('_')
            self.set_compute_result(colours[int(i)], port_key=port_key)

    def visualise(self):
        colours = self.get_compute_result()
        # Draw in vertical grid
        grid = GridNode.helper(None, None, 1, len(colours))
        elements = [RectangleNode.helper(colour) for colour in colours]
        return ShapeRepeaterNode.helper(grid, elements)

    def extract_element(self, parent_group, element_id):
        i = parent_group.get_element_index_from_id(element_id)
        # Add new port definition
        port_id = (PortIO.OUTPUT, f'colour_{i}')
        port_def = PortDef(f"Colour {i}", PT_Colour())
        self._add_port(port_id, port_def) # TODO put this functionality in parent class
        return port_id

    def _is_port_redundant(self, port_id):
        colours = self._prop_val('colour_order')
        _, port_key = port_id
        _, i = port_key.split('_')
        return int(i) >= len(colours)
