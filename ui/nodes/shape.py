import uuid

from cairosvg.shapes import polyline
from numpy.ma.core import indices

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.gradient_datatype import Gradient
from ui.nodes.multi_input_handler import handle_multi_inputs
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode, PropType, PropTypeList, CombinationNode, UnitNodeInfo
from ui.nodes.elem_ref import ElemRef
from ui.nodes.shape_datatypes import Element, Polygon, Ellipse, SineWave, Shape, Polyline
from ui.nodes.utils import process_rgb, rev_process_rgb
from ui.port_defs import PortDef, PortType, PT_Element, PT_Polyline, PT_Gradient, PT_Ellipse, PT_Shape, PT_Fill

SINE_WAVE_NODE_INFO = UnitNodeInfo(
    name="Sine Wave",
    resizable=True,
    selectable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Drawing", PT_Polyline)],
    prop_type_list=PropTypeList(
        [
            PropType("amplitude", "float", default_value=0.5,
                     description="Amplitude of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.", display_name="Amplitude"),
            PropType("wavelength", "float", default_value=1.0, min_value=0.01,
                     description="Wavelength of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.", display_name="Wavelength"),
            PropType("centre_y", "float", default_value=0.5,
                     description="Equilibrium position of the sine wave. With 0° rotation, this is the y-coordinate of the equilibrium position. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.", display_name="Equilibrium position"),
            PropType("phase", "float", default_value=0.0,
                     description="Phase of the sine wave in degrees.", display_name="Phase (°)"),
            PropType("x_min", "float", default_value=0.0,
                     description="Start position of the sine wave. With 0° rotation, this is the x-coordinate of the start of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.", display_name="Wave start"),
            PropType("x_max", "float", default_value=1.0,
                     description="Stop position of the sine wave. With 0° rotation, this is the x-coordinate of the end of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.", display_name="Wave stop"),
            PropType("stroke_width", "float", default_value=1.0,
                     description="Thickness of the line drawing the sine wave.", display_name="Line thickness", min_value=0.0),
            PropType("orientation", "float", default_value=0.0,
                     description="Clockwise rotation applied to the (horizontal) sine wave, set between -180° and +180°.", display_name="Rotation (°)", min_value=-180.0, max_value=180.0),
            PropType("num_points", "int", default_value=100,
                     description="Number of points used to draw the line, set between 2 and 500. The more points used, the more accurate the line is to a sine wave.", min_value=2, max_value=500, display_name="Line resolution")
        ]
    ),
    description="Create part of a sine wave, defining properties such as the amplitude and wavelength. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner."
)


class SineWaveNode(UnitNode):
    UNIT_NODE_INFO = SINE_WAVE_NODE_INFO

    def compute(self):
        try:
            sine_wave = SineWave(self.get_prop_val('amplitude'), self.get_prop_val('wavelength'), self.get_prop_val('centre_y'),
                                     self.get_prop_val('phase'), self.get_prop_val('x_min'), self.get_prop_val('x_max'),
                                     self.get_prop_val('stroke_width'), self.get_prop_val('orientation'),
                                     self.get_prop_val('num_points'))
        except ValueError as e:
            raise NodeInputException(str(e), self.node_id)
        return Element([sine_wave])

    def visualise(self, temp_dir, height, wh_ratio):
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (self.compute(), None)).save()

CUSTOM_LINE_NODE_INFO = UnitNodeInfo(
    name="Custom Line",
    resizable=True,
    selectable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Drawing", PT_Polyline)],
    prop_type_list=PropTypeList(
        [
            PropType("points", "point_table", default_value=[(1, 0), (0, 1)],
                     description="Points defining the path of the line (in order).", display_name="Points"),
            PropType("stroke_width", "float", default_value=1.0,
                                 description="Thickness of the line drawing.", display_name="Line thickness", min_value=0.0)
        ]
    ),
    description="Create a custom line by defining the points the line passes through. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner."
)


class CustomLineNode(UnitNode):
    UNIT_NODE_INFO = CUSTOM_LINE_NODE_INFO

    def compute(self):
        return Element([Polyline(self.get_prop_val('points'), 'black', self.get_prop_val('stroke_width'))])

    def visualise(self, temp_dir, height, wh_ratio):
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (self.compute(), None)).save()

STRAIGHT_LINE_NODE_INFO = UnitNodeInfo(
    name="Straight Line",
    resizable=True,
    selectable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Drawing", PT_Polyline)],
    prop_type_list=PropTypeList(
        [
            PropType("start_coord", "coordinate", default_value=(1, 0),
                     description="Coordinate of the start of the line. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.", display_name="Start coordinate"),
            PropType("stop_coord", "coordinate", default_value=(0, 1),
                     description="Coordinate of the end of the line. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.", display_name="Stop coordinate"),
            PropType("stroke_width", "float", default_value=1.0,
                                 description="Thickness of the straight line.", display_name="Line thickness", min_value=0.0)
        ]
    ),
    description="Create a straight line by defining the start and stop points. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner."
)


class StraightLineNode(UnitNode):
    UNIT_NODE_INFO = STRAIGHT_LINE_NODE_INFO

    def compute(self):
        return Element([Polyline([self.get_prop_val('start_coord'), self.get_prop_val('stop_coord')], 'black', self.get_prop_val('stroke_width'))])

    def visualise(self, temp_dir, height, wh_ratio):
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (self.compute(), None)).save()

POLYGON_NODE_INFO = UnitNodeInfo(
    name="Polygon",
    resizable=True,
    selectable=True,
    in_port_defs=[PortDef("Import Points", PT_Polyline, input_multiple=True, key_name='import_points')],
    prop_port_defs=[PortDef('Colour', PT_Fill, key_name='fill')],
    out_port_defs=[PortDef("Drawing", PT_Element)],
    prop_type_list=PropTypeList(
        [
            PropType("points", "point_table", default_value=[(0, 0), (0, 1), (1, 1)],
                     description="Points defining the path of the polygon edge (in order).", display_name="Points"),
            PropType("fill", "colour", default_value=(0, 0, 0, 255),
                     description="Polygon fill colour.", display_name="Colour", port_modifiable=True)
        ]
    ),
    description="Create a polygon shape by defining the connecting points and deciding the fill colour. Optionally a gradient can be used to fill the shape. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner."
)

class PolygonNode(UnitNode):
    UNIT_NODE_INFO = POLYGON_NODE_INFO

    def compute(self):
        colour = self.get_prop_val('fill')
        if isinstance(colour, Gradient):
            fill = colour
            fill_opacity = 255
        else:
            fill, fill_opacity = process_rgb(self.get_prop_val('fill'))
        # Process input polylines
        handle_multi_inputs(self.get_input_node('import_points'), self.prop_vals['points'])
        # Return element
        return Element([Polygon(self.get_prop_val('points'), fill, fill_opacity)])

    def visualise(self, temp_dir, height, wh_ratio):
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (self.compute(), None)).save()


RECTANGLE_NODE_INFO = UnitNodeInfo(
    name="Rectangle",
    resizable=True,
    selectable=True,
    in_port_defs=[],
    prop_port_defs=[PortDef('Colour', PT_Fill, key_name='fill')],
    out_port_defs=[PortDef("Drawing", PT_Element)],
    prop_type_list=PropTypeList(
        [
            PropType("fill", "colour", default_value=(0, 0, 0, 255),
                     description="Rectangle fill colour.", display_name="Colour", port_modifiable=True)
        ]
    ),
    description="Create a rectangle shape by deciding the fill colour. Optionally a gradient can be used to fill the shape."
)


class RectangleNode(UnitNode):
    UNIT_NODE_INFO = RECTANGLE_NODE_INFO

    @staticmethod
    def helper(fill, fill_opacity):
        return Element([Polygon([(0, 0), (0, 1), (1, 1), (1, 0)], fill, fill_opacity)])

    def compute(self):
        colour = self.get_prop_val('fill')
        if isinstance(colour, Gradient):
            fill = colour
            fill_opacity = 255
        else:
            fill, fill_opacity = process_rgb(self.get_prop_val('fill'))
        return RectangleNode.helper(fill, fill_opacity)

    def visualise(self, temp_dir, height, wh_ratio):
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (self.compute(), None)).save()


ELLIPSE_NODE_INFO = UnitNodeInfo(
    name="Ellipse",
    resizable=True,
    selectable=True,
    in_port_defs=[],
    prop_port_defs=[PortDef('Colour', PT_Fill, key_name='fill')],
    out_port_defs=[PortDef("Drawing", PT_Ellipse)],
    prop_type_list=PropTypeList(
        [
            PropType("rx", "float", default_value=0.5, min_value=0.0,
                     description="Horizontal semi-axis of the ellipse. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.", display_name="Horizontal radius (rx)"),
            PropType("ry", "float", default_value=0.5, min_value=0.0,
                     description="Vertical semi-axis of the ellipse. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.", display_name="Vertical radius (ry)"),
            PropType("centre", "coordinate", default_value=(0.5, 0.5),
                                 description="Coordinate of the ellipse centre. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.", display_name="Centre coordinate"),
            PropType("fill", "colour", default_value=(0, 0, 0, 255),
                     description="Ellipse fill colour.", display_name="Colour", port_modifiable=True),
            PropType("stroke_width", "float", default_value=1.0,
                                 description="Thickness of the line drawing the ellipse border.", display_name="Border thickness", min_value=0.0)
        ]
    ),
    description="Create an ellipse shape. A gradient can be used to fill the shape if required. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner."
)


class EllipseNode(UnitNode):
    UNIT_NODE_INFO = ELLIPSE_NODE_INFO

    def compute(self):
        colour = self.get_prop_val('fill')
        if isinstance(colour, Gradient):
            fill = colour
            fill_opacity = 255
        else:
            fill, fill_opacity = process_rgb(self.get_prop_val('fill'))
        return Element(
            [Ellipse(self.get_prop_val('centre'), (self.get_prop_val('rx'), self.get_prop_val('ry')), fill, fill_opacity, 'black', self.get_prop_val('stroke_width'))])

    def visualise(self, temp_dir, height, wh_ratio):
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (self.compute(), None)).save()

CIRCLE_NODE_INFO = UnitNodeInfo(
    name="Circle",
    resizable=True,
    selectable=True,
    in_port_defs=[],
    prop_port_defs=[PortDef('Colour', PT_Fill, key_name='fill')],
    out_port_defs=[PortDef("Drawing", PT_Ellipse)],
    prop_type_list=PropTypeList(
        [
            PropType("r", "float", default_value=0.5, min_value=0.0,
                     description="Radius of the circle. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.", display_name="Radius"),
            PropType("centre", "coordinate", default_value=(0.5, 0.5),
                                 description="Coordinate of the circle centre. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.", display_name="Centre coordinate"),
            PropType("fill", "colour", default_value=(0, 0, 0, 255),
                     description="Circle fill colour.", display_name="Colour", port_modifiable=True),
            PropType("stroke_width", "float", default_value=1.0,
                                 description="Thickness of the line drawing the circle border.", display_name="Border thickness", min_value=0.0)
        ]
    ),
    description="Create a circle shape. A gradient can be used to fill the shape if required. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner."
)


class CircleNode(UnitNode):
    UNIT_NODE_INFO = CIRCLE_NODE_INFO

    def compute(self):
        colour = self.get_prop_val('fill')
        if isinstance(colour, Gradient):
            fill = colour
            fill_opacity = 255
        else:
            fill, fill_opacity = process_rgb(self.get_prop_val('fill'))
        return Element(
            [Ellipse(self.get_prop_val('centre'), (self.get_prop_val('r'), self.get_prop_val('r')), fill, fill_opacity, 'black', self.get_prop_val('stroke_width'))])

    def visualise(self, temp_dir, height, wh_ratio):
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (self.compute(), None)).save()

ELEMENT_SHAPE_NODE_INFO = UnitNodeInfo(
    name="Shape Drawing",
    resizable=True,
    selectable=False,
    in_port_defs=[],
    out_port_defs=[PortDef("Shape", PT_Shape)],
    prop_type_list=PropTypeList([]),
    description="Immutable drawing extracted from a previously rendered node."
)

class ElementShapeNode(UnitNode):
    UNIT_NODE_INFO = ELEMENT_SHAPE_NODE_INFO

    def compute(self):
        return Element([self.get_prop_val('shape')])

    def visualise(self, temp_dir, height, wh_ratio):
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (self.compute(), None)).save()

ELEMENT_LINE_NODE_INFO = UnitNodeInfo(
    name="Line Drawing",
    resizable=True,
    selectable=False,
    in_port_defs=[],
    out_port_defs=[PortDef("Line", PT_Polyline)],
    prop_type_list=PropTypeList([]),
    description="Immutable drawing extracted from a previously rendered node."
)

class ElementLineNode(UnitNode):
    UNIT_NODE_INFO = ELEMENT_LINE_NODE_INFO

    def compute(self):
        return Element([self.get_prop_val('line')])

    def visualise(self, temp_dir, height, wh_ratio):
        return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (self.compute(), None)).save()

def get_node_from_shape(shape: Shape):
    if isinstance(shape, Polyline):
        return ElementLineNode(
            uuid.uuid4(),
            [],
            {'line': shape.remove_final_scale()}
        )
    else:
        return ElementShapeNode(
            uuid.uuid4(),
            [],
            {'shape': shape.remove_final_scale()}
        )

class ShapeNode(CombinationNode):
    NAME = "Shape"
    SELECTIONS = [PolygonNode, RectangleNode, EllipseNode, CircleNode, SineWaveNode, CustomLineNode, StraightLineNode]
