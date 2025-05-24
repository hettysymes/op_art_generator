from typing import cast

from ui.nodes.gradient_datatype import Gradient
from ui.nodes.node_defs import PrivateNodeInfo, ResolvedProps
from ui.nodes.node_implementations.visualiser import get_rectangle
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode, CombinationNode
from ui.nodes.prop_defs import PropDef, PT_Float, Float, PT_Point, Point, PT_Fill, Colour, PortStatus, Int, PT_Int, \
    List, PT_List, PT_PointsHolder, LineRef, PointsHolder
from ui.nodes.shape_datatypes import Ellipse, SineWave, Polyline, Polygon
from ui.nodes.utils import process_rgb

DEF_SINE_WAVE_INFO = PrivateNodeInfo(
    description="Create part of a sine wave, defining properties such as the amplitude and wavelength. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    prop_defs={
        'amplitude': PropDef(
            prop_type=PT_Float(),
            display_name="Amplitude",
            description="Amplitude of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Float(0.5)
        ),
        'wavelength': PropDef(
            prop_type=PT_Float(min_value=0.001),
            display_name="Wavelength",
            description="Wavelength of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Float(1)
        ),
        'centre_y': PropDef(
            prop_type=PT_Float(),
            display_name="Equilibrium position",
            description="Equilibrium position of the sine wave. With 0° rotation, this is the y-coordinate of the equilibrium position. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Float(0.5)
        ),
        'phase': PropDef(
            prop_type=PT_Float(),
            display_name="Phase (°)",
            description="Phase of the sine wave in degrees.",
            default_value=Float(0)
        ),
        'x_min': PropDef(
            prop_type=PT_Float(),
            display_name="Wave start",
            description="Start position of the sine wave. With 0° rotation, this is the x-coordinate of the start of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Float(0)
        ),
        'x_max': PropDef(
            prop_type=PT_Float(),
            display_name="Wave stop",
            description="Stop position of the sine wave. With 0° rotation, this is the x-coordinate of the end of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Float(1)
        ),
        'stroke_width': PropDef(
            prop_type=PT_Float(min_value=0),
            display_name="Line thickness",
            description="Thickness of the line drawing the sine wave.",
            default_value=Float(1)
        ),
        'orientation': PropDef(
            prop_type=PT_Float(),
            display_name="Rotation (°)",
            description="Clockwise rotation applied to the (horizontal) sine wave.",
            default_value=Float(0)
        ),
        'num_points': PropDef(
            prop_type=PT_Int(min_value=2),
            display_name="Line resolution",
            description="Number of points used to draw the line, (at least 2). The more points used, the more accurate the line is to a sine wave.",
            default_value=Int(100)
        ),
        '_main': PropDef(
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_in_props=False
        )
    }
)


class SineWaveNode(UnitNode):
    NAME = "Sine Wave"
    DEFAULT_NODE_INFO = DEF_SINE_WAVE_INFO

    @staticmethod
    def helper(amplitude, wavelength, centre_y, phase, x_min, x_max, stroke_width=1, num_points=100, orientation=0):
        return SineWave(amplitude, wavelength, centre_y, phase, x_min, x_max, stroke_width, num_points).rotate(
            orientation, (0.5, 0.5))

    def compute(self, props: ResolvedProps, *args):
        try:
            sine_wave = SineWaveNode.helper(props.get('amplitude'), props.get('wavelength'),
                                            props.get('centre_y'),
                                            props.get('phase'), props.get('x_min'),
                                            props.get('x_max'),
                                            props.get('stroke_width'), props.get('num_points'),
                                            props.get('orientation'))
        except ValueError as e:
            raise NodeInputException(e)
        return {'_main': sine_wave}


DEF_CUSTOM_LINE_INFO = PrivateNodeInfo(
    description="Create a custom line by defining the points the line passes through. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    prop_defs={
        'points': PropDef(
            prop_type=PT_List(PT_PointsHolder(), input_multiple=True),
            display_name="Points",
            description="Points defining the path of the line (in order).",
            default_value=List(PT_Point(), [Point(0, 0), Point(0.5, 0.5), Point(1, 0)])
        ),
        'stroke_width': PropDef(
            prop_type=PT_Float(min_value=0),
            display_name="Line thickness",
            description="Thickness of the line drawing.",
            default_value=Float(1)
        ),
        '_main': PropDef(
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_in_props=False
        )
    }
)


class CustomLineNode(UnitNode):
    NAME = "Custom Line"
    DEFAULT_NODE_INFO = DEF_CUSTOM_LINE_INFO

    @staticmethod
    def helper(points, stroke='black', stroke_width=1):
        return Polyline(points, stroke, stroke_width)

    def compute(self, props: ResolvedProps, *args):
        points = List(PT_Point())
        for points_holder in props.get('points'):
            points_holder = cast(PointsHolder, points_holder)
            if isinstance(points_holder, LineRef):
                points.extend(points_holder.points_w_reversal())
            else:
                points.extend(points_holder.points)
        return {'_main': CustomLineNode.helper(points, 'black', props.get('stroke_width'))}


DEF_STRAIGHT_LINE_NODE_INFO = PrivateNodeInfo(
    description="Create a straight line by defining the start and stop points. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    prop_defs={
        'start_coord': PropDef(
            prop_type=PT_Point(),
            display_name="Start coordinate",
            description="Coordinate of the start of the line. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Point(1, 0)
        ),
        'stop_coord': PropDef(
            prop_type=PT_Point(),
            display_name="Stop coordinate",
            description="Coordinate of the end of the line. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Point(0, 1)
        ),
        'stroke_width': PropDef(
            prop_type=PT_Float(min_value=0),
            display_name="Line thickness",
            description="Thickness of the straight line.",
            default_value=Float(1)
        ),
        '_main': PropDef(
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_in_props=False
        )
    }
)


class StraightLineNode(UnitNode):
    NAME = "Straight Line"
    DEFAULT_NODE_INFO = DEF_STRAIGHT_LINE_NODE_INFO

    @staticmethod
    def helper(start_coord: Point, stop_coord: Point, stroke='black', stroke_width=1):
        return Polyline(List(PT_Point(), [start_coord, stop_coord]), stroke, stroke_width)

    def compute(self, props: ResolvedProps, *args):
        return {'_main':
                    StraightLineNode.helper(props.get('start_coord'), props.get('stop_coord'), 'black',
                                            props.get('stroke_width'))}


DEF_POLYGON_INFO = PrivateNodeInfo(
    description="Create a polygon shape by defining the connecting points and deciding the fill colour. Optionally a gradient can be used to fill the shape. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    prop_defs={
        'points': PropDef(
            prop_type=PT_List(PT_PointsHolder(), input_multiple=True),
            display_name="Points",
            description="Points defining the path of the polygon edge (in order).",
            default_value=List(PT_PointsHolder(), [Point(0, 0), Point(0, 1), Point(1, 1)]),
        ),
        'fill': PropDef(
            prop_type=PT_Fill(),
            display_name="Fill",
            description="Polygon fill colour.",
            default_value=Colour(0, 0, 0, 255)
        ),
        'stroke_width': PropDef(
            prop_type=PT_Float(min_value=0),
            display_name="Border thickness",
            description="Thickness of the line drawing the polygon border.",
            default_value=Float(1)
        ),
        '_main': PropDef(
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_in_props=False
        )
    }
)


class PolygonNode(UnitNode):
    NAME = "Polygon"
    DEFAULT_NODE_INFO = DEF_POLYGON_INFO

    def compute(self, props: ResolvedProps, *args):
        points = List(PT_Point())
        for points_holder in props.get('points'):
            points_holder = cast(PointsHolder, points_holder)
            if isinstance(points_holder, LineRef):
                points.extend(points_holder.points_w_reversal())
            else:
                points.extend(points_holder.points)
        # Return polygon
        return {'_main': Polygon(points, props.get('fill'),'none',
                                     props.get('stroke_width'))}


DEF_RECTANGLE_NODE_INFO = PrivateNodeInfo(
    description="Create a square shape by deciding the fill colour. Optionally a gradient can be used to fill the shape.",
    prop_defs={
        'fill': PropDef(
            prop_type=PT_Fill(),
            display_name="Fill",
            description="Square fill colour.",
            default_value=Colour(0, 0, 0, 255)
        ),
        '_main': PropDef(
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_in_props=False
        )
    }
)


class RectangleNode(UnitNode):
    NAME = "Square"
    DEFAULT_NODE_INFO = DEF_RECTANGLE_NODE_INFO

    def compute(self, props: ResolvedProps, *args):
        return {'_main': get_rectangle(props.get('fill'), 'none', 1)}


DEF_ELLIPSE_INFO = PrivateNodeInfo(
    description="Create an ellipse shape. A gradient can be used to fill the shape if required. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    prop_defs={
        'rx': PropDef(
            prop_type=PT_Float(min_value=0),
            display_name="Horizontal radius (rx)",
            description="Horizontal semi-axis of the ellipse. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Float(0.5)
        ),
        'ry': PropDef(
            prop_type=PT_Float(min_value=0),
            display_name="Vertical radius (ry)",
            description="Vertical semi-axis of the ellipse. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Float(0.5)
        ),
        'centre': PropDef(
            prop_type=PT_Point(),
            display_name="Centre coordinate",
            description="Coordinate of the ellipse centre. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Point(0.5, 0.5)
        ),
        'fill': PropDef(
            prop_type=PT_Fill(),
            display_name="Colour",
            description="Ellipse fill colour.",
            default_value=Colour(0, 0, 0, 255),
            input_port_status=PortStatus.OPTIONAL
        ),
        'stroke_width': PropDef(
            prop_type=PT_Float(min_value=0),
            display_name="Border thickness",
            description="Thickness of the line drawing the ellipse border.",
            default_value=Float(1)
        ),
        '_main': PropDef(
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_in_props=False
        )
    }
)


#
class EllipseNode(UnitNode):
    NAME = "Ellipse"
    DEFAULT_NODE_INFO = DEF_ELLIPSE_INFO

    @staticmethod
    def helper(colour, centre, radius, stroke='none', stroke_width=1):
        if isinstance(colour, Gradient):
            fill = colour
            fill_opacity = 255
        else:
            fill, fill_opacity = process_rgb(colour)
        return Ellipse(centre, radius, fill,
                       fill_opacity, stroke, stroke_width)

    def compute(self, props: ResolvedProps, *args):
        return {'_main': EllipseNode.helper(props.get('fill'), props.get('centre'),
                                            (props.get('rx'), props.get('ry')),
                                            'none', props.get('stroke_width'))}


DEF_CIRCLE_INFO = PrivateNodeInfo(
    description="Create a circle shape. A gradient can be used to fill the shape if required. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    prop_defs={
        'r': PropDef(
            prop_type=PT_Float(min_value=0),
            display_name="Radius",
            description="Radius of the circle. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Float(0.5)
        ),
        'centre': PropDef(
            prop_type=PT_Point(),
            display_name="Centre coordinate",
            description="Coordinate of the circle centre. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Point(0.5, 0.5)
        ),
        'fill': PropDef(
            prop_type=PT_Fill(),
            display_name="Colour",
            description="Circle fill colour.",
            default_value=Colour(0, 0, 0, 255)
        ),
        'stroke_width': PropDef(
            prop_type=PT_Float(min_value=0),
            display_name="Border thickness",
            description="Thickness of the line drawing the circle border.",
            default_value=Float(0.5)
        ),
        '_main': PropDef(
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_in_props=False
        )
    }
)


def ellipse_helper(fill, centre, radius, stroke='none', stroke_width=1.0):
    if isinstance(fill, Gradient):
        fill = fill
        fill_opacity = 255
    else:
        fill, fill_opacity = process_rgb(fill)
    return Ellipse(centre, radius, fill,
                   fill_opacity, stroke, stroke_width)


class CircleNode(UnitNode):
    NAME = "Circle"
    DEFAULT_NODE_INFO = DEF_CIRCLE_INFO

    @staticmethod
    def helper(colour, centre, radius, stroke='none', stroke_width=Float(1.0)):
        return ellipse_helper(colour, centre, (radius, radius), stroke, stroke_width)

    def compute(self, props: ResolvedProps, *args):
        return {'_main': CircleNode.helper(props.get('fill'),
                                           props.get('centre'),
                                           props.get('r'),
                                           'none',
                                           props.get('stroke_width'))}


class ShapeNode(CombinationNode):
    NAME = "Shape"
    SELECTIONS = [PolygonNode, RectangleNode, EllipseNode, CircleNode, SineWaveNode, StraightLineNode, CustomLineNode]
