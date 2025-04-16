from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, PropType, PropTypeList, CombinationNode, UnitNodeInfo
from ui.nodes.shape_datatypes import Element, Polygon, Ellipse
from ui.port_defs import PortDef, PortType

POLYGON_NODE_INFO = UnitNodeInfo(
    name="Polygon",
    resizable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList(
        [
            PropType("points", "table", default_value=[(0, 0), (0, 1), (1, 1)],
                     description=""),
            PropType("fill", "string", default_value="black",
                     description="")
        ]
    )
)


class PolygonNode(UnitNode):
    UNIT_NODE_INFO = POLYGON_NODE_INFO

    def compute(self):
        return Element([Polygon(self.prop_vals['points'], self.prop_vals['fill'], 'none')])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()


RECTANGLE_NODE_INFO = UnitNodeInfo(
    name="Rectangle",
    resizable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList(
        [
            PropType("fill", "string", default_value="black",
                     description="")
        ]
    )
)


class RectangleNode(UnitNode):
    UNIT_NODE_INFO = RECTANGLE_NODE_INFO

    def compute(self):
        return Element([Polygon([(0, 0), (0, 1), (1, 1), (1, 0)], self.prop_vals['fill'], 'none')])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()


ELLIPSE_NODE_INFO = UnitNodeInfo(
    name="Ellipse",
    resizable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList(
        [
            PropType("rx", "float", default_value=0.5,
                     description=""),
            PropType("ry", "float", default_value=0.5,
                     description=""),
            PropType("fill", "string", default_value="black",
                     description="")
        ]
    )
)


class EllipseNode(UnitNode):
    UNIT_NODE_INFO = ELLIPSE_NODE_INFO

    def compute(self):
        return Element(
            [Ellipse((0.5, 0.5), (self.prop_vals['rx'], self.prop_vals['ry']), self.prop_vals['fill'], 'none')])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()


class ShapeNode(CombinationNode):
    NAME = "Shape"
    SELECTIONS = [PolygonNode, RectangleNode, EllipseNode]
