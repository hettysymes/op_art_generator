from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, PropType, PropTypeList, CombinationNode
from ui.nodes.shape_datatypes import Element, Polygon, Ellipse
from ui.port_defs import PortDef, PortType


class PolygonNode(UnitNode):
    DISPLAY = "Polygon"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = PolygonNode.DISPLAY
        self.resizable = True
        self.in_port_defs = []
        self.out_port_defs = [PortDef("Drawing", PortType.ELEMENT)]
        self.prop_type_list = PropTypeList(
            [
                PropType("points", "table", default_value=[(0, 0), (0, 1), (1, 1)],
                         description=""),
                PropType("fill", "string", default_value="black",
                         description="")
            ]
        )

    def compute(self):
        return Element([Polygon(self.prop_vals['points'], self.prop_vals['fill'], 'none')])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()


class RectangleNode(UnitNode):
    DISPLAY = "Rectangle"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = RectangleNode.DISPLAY
        self.resizable = True
        self.in_port_defs = []
        self.out_port_defs = [PortDef("Drawing", PortType.ELEMENT)]
        self.prop_type_list = PropTypeList(
            [
                PropType("fill", "string", default_value="black",
                         description="")
            ]
        )

    def compute(self):
        return Element([Polygon([(0, 0), (0, 1), (1, 1), (1, 0)], self.prop_vals['fill'], 'none')])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()


class EllipseNode(UnitNode):
    DISPLAY = "Ellipse"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = EllipseNode.DISPLAY
        self.resizable = True
        self.in_port_defs = []
        self.out_port_defs = [PortDef("Drawing", PortType.ELEMENT)]
        self.prop_type_list = PropTypeList(
            [
                PropType("rx", "float", default_value=0.5,
                         description=""),
                PropType("ry", "float", default_value=0.5,
                         description=""),
                PropType("fill", "string", default_value="black",
                         description="")
            ]
        )

    def compute(self):
        return Element(
            [Ellipse((0.5, 0.5), (self.prop_vals['rx'], self.prop_vals['ry']), self.prop_vals['fill'], 'none')])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()


class ShapeNode(CombinationNode):
    DISPLAY = "Shape"
    SELECTIONS = [PolygonNode, RectangleNode, EllipseNode]

    def __init__(self, node_id, input_nodes, properties, selection_index):
        super().__init__(node_id, input_nodes, properties, selection_index)

    def init_selections(self):
        self.selections = ShapeNode.SELECTIONS
