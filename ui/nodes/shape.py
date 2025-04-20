from PyQt5.QtCore import Qt

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, PropType, PropTypeList, CombinationNode, UnitNodeInfo
from ui.nodes.shape_datatypes import Element, Polygon, Ellipse, SineWave
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
            PropType("fill", "colour", default_value="#000000",
                     description="")
        ]
    )
)


class PolygonNode(UnitNode):
    UNIT_NODE_INFO = POLYGON_NODE_INFO

    def compute(self):
        return Element([Polygon(self.prop_vals['points'], self.prop_vals['fill'])])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()


RECTANGLE_NODE_INFO = UnitNodeInfo(
    name="Rectangle",
    resizable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList(
        [
            PropType("fill", "colour", default_value="#000000",
                     description="")
        ]
    )
)


class RectangleNode(UnitNode):
    UNIT_NODE_INFO = RECTANGLE_NODE_INFO

    def compute(self):
        return Element([Polygon([(0, 0), (0, 1), (1, 1), (1, 0)], self.prop_vals['fill'])])

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
            PropType("fill", "colour", default_value="#000000",
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


SINE_WAVE_NODE_INFO = UnitNodeInfo(
    name="Sine Wave",
    resizable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList(
        [
            PropType("amplitude", "float", default_value=0.5,
                     description=""),
            PropType("wavelength", "float", default_value=1.0,
                     description=""),
            PropType("centre_y", "float", default_value=0.5,
                     description=""),
            PropType("phase", "float", default_value=0.0,
                     description="", min_value=-360, max_value=360),
            PropType("x_min", "float", default_value=0.0,
                     description=""),
            PropType("x_max", "float", default_value=1.0,
                     description=""),
            PropType("stroke_width", "float", default_value=1.0,
                     description="", min_value=0.0),
            PropType("orientation", "float", default_value=0.0,
                     description="", min_value=-360.0, max_value=360.0),
            PropType("num_points", "int", default_value=100,
                     description="", min_value=2, max_value=500, display_name="line resolution")
        ]
    )
)


class SineWaveNode(UnitNode):
    UNIT_NODE_INFO = SINE_WAVE_NODE_INFO

    def compute(self):
        return Element([SineWave(self.prop_vals['amplitude'], self.prop_vals['wavelength'], self.prop_vals['centre_y'],
                                 self.prop_vals['phase'], self.prop_vals['x_min'], self.prop_vals['x_max'],
                                 self.prop_vals['stroke_width'], self.prop_vals['orientation'],
                                 self.prop_vals['num_points'])])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()


class ShapeNode(CombinationNode):
    NAME = "Shape"
    SELECTIONS = [PolygonNode, RectangleNode, EllipseNode, SineWaveNode]
