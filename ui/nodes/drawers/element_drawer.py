from ui.nodes.drawers.Drawing import Drawing
from ui.nodes.shape_datatypes import Element, Group


class ElementDrawer(Drawing):

    def __init__(self, out_name, height, wh_ratio, inputs):
        super().__init__(out_name, height, wh_ratio)
        self.group_node_output, self.bg_col = inputs
        assert isinstance(self.group_node_output, Group)
        assert not self.group_node_output.transform_list.transforms

    def draw(self):
        if self.bg_col is not None:
            self.add_bg(self.bg_col)
        print(f"INPUT:")
        print(self.group_node_output)
        print()
        drawn_elem = Group(uid=self.group_node_output.uid)
        for element in self.group_node_output:
            drawn_elem.add(element.scale(self.width, self.height))
        print(f"OUTPUT:")
        print(drawn_elem)
        print()
        self.dwg_add(drawn_elem.get(self.dwg))
