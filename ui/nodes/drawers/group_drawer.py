from ui_old.nodes.drawers.Drawing import Drawing
from ui_old.nodes.shape_datatypes import Group


class GroupDrawer(Drawing):

    def __init__(self, filepath, width, height, inputs):
        super().__init__(filepath, width, height)
        self.group_node_output, self.bg_col = inputs
        assert isinstance(self.group_node_output, Group)
        assert not self.group_node_output.transform_list.transforms

    def draw(self):
        self.dwg.viewbox(0, 0, 1, 1)
        if self.bg_col is not None:
            self.add_bg(self.bg_col)
        # print(f"DRAWN ELEM:")
        # print(self.group_node_output)
        # print()
        self.dwg_add(self.group_node_output.get(self.dwg))
