import uuid

from cairosvg.shapes import polyline
from numpy.ma.core import indices

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.multi_input_handler import handle_multi_inputs
from ui.nodes.nodes import UnitNode, PropType, PropTypeList, CombinationNode, UnitNodeInfo
from ui.nodes.elem_ref import ElemRef
from ui.nodes.shape_datatypes import Element, Polygon, Ellipse, SineWave, Shape
from ui.nodes.utils import process_rgb, rev_process_rgb
from ui.port_defs import PortDef, PortType

SINE_WAVE_NODE_INFO = UnitNodeInfo(
    name="Sine Wave",
    resizable=True,
    selectable=True,
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

    def visualise(self, temp_dir, height, wh_ratio):
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (self.compute(), None)).save()

POLYGON_NODE_INFO = UnitNodeInfo(
    name="Polygon",
    resizable=True,
    selectable=True,
    in_port_defs=[PortDef("Gradient", PortType.GRADIENT), PortDef("Import Points", PortType.ELEMENT, input_multiple=True)],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList(
        [
            PropType("points", "point_table", default_value=[(0, 0), (0, 1), (1, 1)],
                     description=""),
            PropType("fill", "colour", default_value=(0, 0, 0, 255),
                     description="")
        ]
    )
)

class PolygonNode(UnitNode):
    UNIT_NODE_INFO = POLYGON_NODE_INFO

    def compute(self):
        gradient = self.input_nodes[0].compute()
        if gradient:
            fill = gradient
            fill_opacity = 255
        else:
            fill, fill_opacity = process_rgb(self.prop_vals['fill'])
        # Process input polylines
        handle_multi_inputs(self.input_nodes[1:], self.prop_vals['points'])
        # Return element
        return Element([Polygon(self.prop_vals['points'], fill, fill_opacity)])

    def visualise(self, temp_dir, height, wh_ratio):
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (self.compute(), None)).save()


RECTANGLE_NODE_INFO = UnitNodeInfo(
    name="Rectangle",
    resizable=True,
    selectable=True,
    in_port_defs=[PortDef("Gradient", PortType.GRADIENT)],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList(
        [
            PropType("fill", "colour", default_value=(0, 0, 0, 255),
                     description="")
        ]
    )
)


class RectangleNode(UnitNode):
    UNIT_NODE_INFO = RECTANGLE_NODE_INFO

    def compute(self):
        gradient = self.input_nodes[0].compute()
        if gradient:
            fill = gradient
            fill_opacity = 255
        else:
            fill, fill_opacity = process_rgb(self.prop_vals['fill'])
        return Element([Polygon([(0, 0), (0, 1), (1, 1), (1, 0)], fill, fill_opacity)])

    def visualise(self, temp_dir, height, wh_ratio):
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (self.compute(), None)).save()


ELLIPSE_NODE_INFO = UnitNodeInfo(
    name="Ellipse",
    resizable=True,
    selectable=True,
    in_port_defs=[PortDef("Gradient", PortType.GRADIENT)],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList(
        [
            PropType("rx", "float", default_value=0.5,
                     description=""),
            PropType("ry", "float", default_value=0.5,
                     description=""),
            PropType("cx", "float", default_value=0.5,
                                 description=""),
            PropType("cy", "float", default_value=0.5,
                                 description=""),
            PropType("fill", "colour", default_value=(0, 0, 0, 255),
                     description=""),
            PropType("stroke_width", "float", default_value=1.0,
                                 description="", min_value=0.0)
        ]
    )
)


class EllipseNode(UnitNode):
    UNIT_NODE_INFO = ELLIPSE_NODE_INFO

    def compute(self):
        gradient = self.input_nodes[0].compute()
        if gradient:
            fill = gradient
            fill_opacity = 255
        else:
            fill, fill_opacity = process_rgb(self.prop_vals['fill'])
        return Element(
            [Ellipse((self.prop_vals['cx'], self.prop_vals['cy']), (self.prop_vals['rx'], self.prop_vals['ry']), fill, fill_opacity, 'black', self.prop_vals['stroke_width'])])

    def visualise(self, temp_dir, height, wh_ratio):
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (self.compute(), None)).save()

CIRCLE_NODE_INFO = UnitNodeInfo(
    name="Circle",
    resizable=True,
    selectable=True,
    in_port_defs=[PortDef("Gradient", PortType.GRADIENT)],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList(
        [
            PropType("r", "float", default_value=0.5,
                     description=""),
            PropType("cx", "float", default_value=0.5,
                                 description=""),
            PropType("cy", "float", default_value=0.5,
                                 description=""),
            PropType("fill", "colour", default_value=(0, 0, 0, 255),
                     description=""),
            PropType("stroke_width", "float", default_value=1.0,
                                 description="", min_value=0.0)
        ]
    )
)


class CircleNode(UnitNode):
    UNIT_NODE_INFO = CIRCLE_NODE_INFO

    def compute(self):
        gradient = self.input_nodes[0].compute()
        if gradient:
            fill = gradient
            fill_opacity = 255
        else:
            fill, fill_opacity = process_rgb(self.prop_vals['fill'])
        return Element(
            [Ellipse((self.prop_vals['cx'], self.prop_vals['cy']), (self.prop_vals['r'], self.prop_vals['r']), fill, fill_opacity, 'black', self.prop_vals['stroke_width'])])

    def visualise(self, temp_dir, height, wh_ratio):
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (self.compute(), None)).save()

ELEMENT_NODE_INFO = UnitNodeInfo(
    name="Drawing",
    resizable=True,
    selectable=False,
    in_port_defs=[],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList([])
)

class ElementNode(UnitNode):
    UNIT_NODE_INFO = ELEMENT_NODE_INFO

    def compute(self):
        return Element([self.prop_vals['shape']])

    def visualise(self, temp_dir, height, wh_ratio):
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (self.compute(), None)).save()

def get_node_from_shape(shape: Shape):
    return ElementNode(
        uuid.uuid4(),
        [],
        {'shape': shape.remove_final_scale()}
    )

class ShapeNode(CombinationNode):
    NAME = "Shape"
    SELECTIONS = [PolygonNode, RectangleNode, EllipseNode, CircleNode, SineWaveNode]
