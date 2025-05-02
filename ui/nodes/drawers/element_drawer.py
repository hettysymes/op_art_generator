from ui.nodes.drawers.Drawing import Drawing
from ui.nodes.shape_datatypes import Group


class ElementDrawer(Drawing):

    def __init__(self, out_name, height, wh_ratio, inputs):
        super().__init__(out_name, height, wh_ratio)
        self.group_node_output, self.bg_col = inputs
        assert isinstance(self.group_node_output, Group)
        assert not self.group_node_output.transform_list.transforms

    def draw(self):
        if self.bg_col is not None:
            self.add_bg(self.bg_col)
        # debug_info = self.group_node_output.debug_info if self.group_node_output.debug_info else ""
        # drawn_elem = Group(uid=self.group_node_output.uid, debug_info=f"{debug_info} (scaled)")
        # for element in self.group_node_output:
        #     drawn_elem.add(element.scale(self.width, self.height))
        print(f"DRAWN ELEM:")
        print(self.group_node_output)
        print()
        self.dwg_add(self.group_node_output.get(self.dwg))
