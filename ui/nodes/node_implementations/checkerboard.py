from ui.nodes.node_defs import NodeInfo
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Grid, PT_Element
from ui.nodes.shape_datatypes import Group
from ui.nodes.transforms import Scale, Translate

DEF_CHECKERBOARD_INFO = NodeInfo(
    description="Create a checkerboard pattern from a grid and two drawings. The two drawings are placed alternately in a checkerboard pattern on the grid.",
    port_defs={
        (PortIO.INPUT, 'grid'): PortDef("Grid", PT_Grid),
        (PortIO.INPUT, 'elem1'): PortDef("Drawing 1", PT_Element),
        (PortIO.INPUT, 'elem2'): PortDef("Drawing 2", PT_Element),
        (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Element)
    },
    prop_entries={}
)


class CheckerboardNode(UnitNode):
    NAME = "Checkerboard"
    DEFAULT_NODE_INFO = DEF_CHECKERBOARD_INFO

    @staticmethod
    def helper(grid, element1=None, element2=None):
        assert element1 or element2
        v_line_xs, h_line_ys = grid
        ret_group = Group(debug_info="Checkerboard")
        element1_starts = True
        for i in range(1, len(v_line_xs)):
            element1_turn = element1_starts
            for j in range(1, len(h_line_ys)):
                x1 = v_line_xs[i - 1]
                x2 = v_line_xs[i]
                y1 = h_line_ys[j - 1]
                y2 = h_line_ys[j]
                element = element1 if element1_turn else element2
                if element:
                    cell_group = Group([Scale(x2 - x1, y2 - y1), Translate(x1, y1)], debug_info=f"Cell ({j},{i})")
                    cell_group.add(element)
                    ret_group.add(cell_group)
                element1_turn = not element1_turn
            element1_starts = not element1_starts
        return ret_group

    def compute(self, out_port_key='_main'):
        grid = self._prop_val('grid')
        element1 = self._prop_val('elem1')
        element2 = self._prop_val('elem2')
        if grid and (element1 or element2):
            return CheckerboardNode.helper(grid, element1, element2)
        return None
