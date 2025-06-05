import math
from typing import cast

from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory, DisplayStatus
from nodes.node_implementations.blaze_maker import BlazeMakerNode
from nodes.node_implementations.visualiser import get_rectangle
from nodes.node_input_exception import NodeInputException
from nodes.nodes import UnitNode, CombinationNode
from nodes.prop_types import PT_Number, PT_Point, PT_Fill, PT_Int, \
    PT_List, PT_PointsHolder, PT_Polyline, PT_Polygon, PT_Ellipse
from nodes.prop_values import List, Int, Float, PointsHolder, Point, Colour, LineRef
from nodes.shape_datatypes import Ellipse, Polyline, Polygon

DEF_SINE_WAVE_INFO = PrivateNodeInfo(
    description="Create part of a sine wave, defining properties such as the amplitude and wavelength. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    prop_defs={
        'amplitude': PropDef(
            prop_type=PT_Number(),
            display_name="Amplitude",
            description="Amplitude of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Float(0.5)
        ),
        'wavelength': PropDef(
            prop_type=PT_Number(min_value=0.001),
            display_name="Wavelength",
            description="Wavelength of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Float(1)
        ),
        'centre_y': PropDef(
            prop_type=PT_Number(),
            display_name="Equilibrium position",
            description="Equilibrium position of the sine wave. With 0° rotation, this is the y-coordinate of the equilibrium position. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Float(0.5)
        ),
        'phase': PropDef(
            prop_type=PT_Number(),
            display_name="Phase (°)",
            description="Phase of the sine wave in degrees.",
            default_value=Float(0)
        ),
        'x_min': PropDef(
            prop_type=PT_Number(),
            display_name="Wave start",
            description="Start position of the sine wave. With 0° rotation, this is the x-coordinate of the start of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Float(0)
        ),
        'x_max': PropDef(
            prop_type=PT_Number(),
            display_name="Wave stop",
            description="Stop position of the sine wave. With 0° rotation, this is the x-coordinate of the end of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Float(1)
        ),
        'orientation': PropDef(
            prop_type=PT_Number(),
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
        'stroke_width': PropDef(
            prop_type=PT_Number(min_value=0),
            display_name="Line thickness",
            description="Thickness of the line drawing the sine wave.",
            default_value=Float(1)
        ),
        'stroke_colour': PropDef(
            prop_type=PT_Fill(),
            display_name="Line colour",
            description="Colour of the line.",
            default_value=Colour(0, 0, 0, 255)
        ),
        '_main': PropDef(
            prop_type=PT_Polyline(),
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class SineWaveNode(UnitNode):
    NAME = "Sine Wave"
    NODE_CATEGORY = NodeCategory.SOURCE
    DEFAULT_NODE_INFO = DEF_SINE_WAVE_INFO

    @staticmethod
    def helper(amplitude, wavelength, centre_y, phase, x_min, x_max, stroke_width=1, stroke=Colour(), num_points=100,
               orientation=0):
        if x_min > x_max:
            raise ValueError("Wave start position must be smaller than wave stop position.")
        points = List(PT_Point())

        # Generate 100 evenly spaced x-values between x_min and x_max
        x_values = [x_min + i * (x_max - x_min) / (num_points - 1) for i in range(num_points)]

        # Calculate corresponding y-values using the sine wave formula
        for x in x_values:
            # Standard sine wave equation: y = A * sin(2π * x / λ + φ) + centre_y
            # where A is amplitude, λ is wavelength, and φ is phase
            y = amplitude * math.sin(2 * math.pi * x / wavelength + math.radians(phase)) + centre_y
            points.append(Point(x, y))

        return Polyline(points, stroke, stroke_width).rotate(orientation, (0.5, 0.5))

    def compute(self, props: ResolvedProps, *args):
        try:
            sine_wave = SineWaveNode.helper(props.get('amplitude'), props.get('wavelength'),
                                            props.get('centre_y'),
                                            props.get('phase'), props.get('x_min'),
                                            props.get('x_max'),
                                            props.get('stroke_width'), props.get('stroke_colour'),
                                            props.get('num_points'),
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
            prop_type=PT_Number(min_value=0),
            display_name="Line thickness",
            description="Thickness of the line drawing.",
            default_value=Float(1)
        ),
        'stroke_colour': PropDef(
            prop_type=PT_Fill(),
            display_name="Line colour",
            description="Colour of the line.",
            default_value=Colour(0, 0, 0, 255)
        ),
        '_main': PropDef(
            prop_type=PT_Polyline(),
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class CustomLineNode(UnitNode):
    NAME = "Custom Line"
    NODE_CATEGORY = NodeCategory.SOURCE
    DEFAULT_NODE_INFO = DEF_CUSTOM_LINE_INFO

    @staticmethod
    def helper(points, stroke=Colour(0, 0, 0, 255), stroke_width=1):
        return Polyline(points, stroke, stroke_width)

    def compute(self, props: ResolvedProps, *args):
        points = List(PT_Point())
        for points_holder in props.get('points'):
            points_holder = cast(PointsHolder, points_holder)
            if isinstance(points_holder, LineRef):
                points.extend(points_holder.points_w_reversal())
            else:
                points.extend(points_holder.points)
        return {'_main': CustomLineNode.helper(points, props.get('stroke_colour'), props.get('stroke_width'))}


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
            prop_type=PT_Number(min_value=0),
            display_name="Line thickness",
            description="Thickness of the straight line.",
            default_value=Float(1)
        ),
        'stroke_colour': PropDef(
            prop_type=PT_Fill(),
            display_name="Line colour",
            description="Colour of the line.",
            default_value=Colour(0, 0, 0, 255)
        ),
        '_main': PropDef(
            prop_type=PT_Polyline(),
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class StraightLineNode(UnitNode):
    NAME = "Straight Line"
    NODE_CATEGORY = NodeCategory.SOURCE
    DEFAULT_NODE_INFO = DEF_STRAIGHT_LINE_NODE_INFO

    @staticmethod
    def helper(start_coord: Point, stop_coord: Point, stroke=Colour(0, 0, 0, 255), stroke_width=1):
        return Polyline(List(PT_Point(), [start_coord, stop_coord]), stroke, stroke_width)

    def compute(self, props: ResolvedProps, *args):
        return {'_main':
                    StraightLineNode.helper(props.get('start_coord'), props.get('stop_coord'),
                                            props.get('stroke_colour'),
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
            prop_type=PT_Number(min_value=0),
            display_name="Border thickness",
            description="Thickness of the line drawing the polygon border.",
            default_value=Float(0)
        ),
        'stroke_colour': PropDef(
            prop_type=PT_Fill(),
            display_name="Border colour",
            description="Colour of the polygon border.",
            default_value=Colour()
        ),
        '_main': PropDef(
            prop_type=PT_Polygon(),
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class PolygonNode(UnitNode):
    NAME = "Polygon"
    NODE_CATEGORY = NodeCategory.SOURCE
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
        return {'_main': Polygon(points, props.get('fill'), props.get('stroke_colour'),
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
        'stroke_width': PropDef(
            prop_type=PT_Number(min_value=0),
            display_name="Border thickness",
            description="Thickness of the line drawing the square border.",
            default_value=Float(0)
        ),
        'stroke_colour': PropDef(
            prop_type=PT_Fill(),
            display_name="Border colour",
            description="Colour of the square border.",
            default_value=Colour()
        ),
        '_main': PropDef(
            prop_type=PT_Polygon(),
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class RectangleNode(UnitNode):
    NAME = "Square"
    NODE_CATEGORY = NodeCategory.SOURCE
    DEFAULT_NODE_INFO = DEF_RECTANGLE_NODE_INFO

    def compute(self, props: ResolvedProps, *args):
        return {'_main': get_rectangle(props.get('fill'), props.get('stroke_colour'), props.get('stroke_width'))}


DEF_ELLIPSE_INFO = PrivateNodeInfo(
    description="Create an ellipse shape. A gradient can be used to fill the shape if required. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    prop_defs={
        'rx': PropDef(
            prop_type=PT_Number(min_value=0),
            display_name="Horizontal radius (rx)",
            description="Horizontal semi-axis of the ellipse. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
            default_value=Float(0.3)
        ),
        'ry': PropDef(
            prop_type=PT_Number(min_value=0),
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
        'orientation': PropDef(
            prop_type=PT_Number(),
            display_name="Rotation (°)",
            description="Clockwise rotation applied to the ellipse.",
            default_value=Float(0)
        ),
        'fill': PropDef(
            prop_type=PT_Fill(),
            display_name="Colour",
            description="Ellipse fill colour.",
            default_value=Colour(0, 0, 0, 255),
            input_port_status=PortStatus.OPTIONAL
        ),
        'stroke_width': PropDef(
            prop_type=PT_Number(min_value=0),
            display_name="Border thickness",
            description="Thickness of the line drawing the ellipse border.",
            default_value=Float(0)
        ),
        'stroke_colour': PropDef(
            prop_type=PT_Fill(),
            display_name="Border colour",
            description="Colour of the ellipse border.",
            default_value=Colour()
        ),
        '_main': PropDef(
            prop_type=PT_Ellipse(),
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class EllipseNode(UnitNode):
    NAME = "Ellipse"
    NODE_CATEGORY = NodeCategory.SOURCE
    DEFAULT_NODE_INFO = DEF_ELLIPSE_INFO

    def compute(self, props: ResolvedProps, *args):
        return {'_main': Ellipse(props.get('centre'), (props.get('rx'), props.get('ry')), props.get('fill'),
                                 props.get('stroke_colour'),
                                 props.get('stroke_width')).rotate(props.get('orientation'), (0.5, 0.5))}


DEF_CIRCLE_INFO = PrivateNodeInfo(
    description="Create a circle shape. A gradient can be used to fill the shape if required. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    prop_defs={
        'r': PropDef(
            prop_type=PT_Number(min_value=0),
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
            prop_type=PT_Number(min_value=0),
            display_name="Border thickness",
            description="Thickness of the line drawing the circle border.",
            default_value=Float(0)
        ),
        'stroke_colour': PropDef(
            prop_type=PT_Fill(),
            display_name="Border colour",
            description="Colour of the circle border.",
            default_value=Colour()
        ),
        '_main': PropDef(
            prop_type=PT_Ellipse(),
            display_name="Drawing",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class CircleNode(UnitNode):
    NAME = "Circle"
    NODE_CATEGORY = NodeCategory.SOURCE
    DEFAULT_NODE_INFO = DEF_CIRCLE_INFO

    def compute(self, props: ResolvedProps, *args):
        r = props.get('r')
        return {'_main': Ellipse(props.get('centre'), (r, r), props.get('fill'), props.get('stroke_colour'),
                                 props.get('stroke_width'))}


class ShapeNode(CombinationNode):
    NAME = "Source"
    NODE_CATEGORY = NodeCategory.SOURCE
    SELECTIONS = [PolygonNode, RectangleNode, EllipseNode, CircleNode, SineWaveNode, StraightLineNode, CustomLineNode, BlazeMakerNode]
