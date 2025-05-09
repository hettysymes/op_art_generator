from ui.nodes.gradient_datatype import Gradient
from ui.nodes.node_defs import NodeInfo, PropType, PropEntry
from ui.nodes.node_input_exception import NodeInputException
from ui.nodes.nodes import UnitNode, CombinationNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Polyline, PT_Fill, PT_Element, PT_Ellipse
from ui.nodes.shape_datatypes import Polygon, Group, Polyline, SineWave, Ellipse
from ui.nodes.utils import process_rgb

DEF_SINE_WAVE_INFO = NodeInfo(
    description="Create part of a sine wave, defining properties such as the amplitude and wavelength. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    port_defs={
        (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Polyline)
    },
    prop_entries={
        'amplitude': PropEntry(PropType.FLOAT,
                               display_name="Amplitude",
                               description="Amplitude of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
                               default_value=0.5),
        'wavelength': PropEntry(PropType.FLOAT,
                                display_name="Wavelength",
                                description="Wavelength of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
                                default_value=1.0,
                                min_value=0.01),
        'centre_y': PropEntry(PropType.FLOAT,
                              display_name="Equilibrium position",
                              description="Equilibrium position of the sine wave. With 0° rotation, this is the y-coordinate of the equilibrium position. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
                              default_value=0.5),
        'phase': PropEntry(PropType.FLOAT,
                           display_name="Phase (°)",
                           description="Phase of the sine wave in degrees.",
                           default_value=0.0),
        'x_min': PropEntry(PropType.FLOAT,
                           display_name="Wave start",
                           description="Start position of the sine wave. With 0° rotation, this is the x-coordinate of the start of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
                           default_value=0.0),
        'x_max': PropEntry(PropType.FLOAT,
                           display_name="Wave stop",
                           description="Stop position of the sine wave. With 0° rotation, this is the x-coordinate of the end of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
                           default_value=1.0),
        'stroke_width': PropEntry(PropType.FLOAT,
                                  display_name="Line thickness",
                                  description="Thickness of the line drawing the sine wave.",
                                  default_value=1.0,
                                  min_value=0.0),
        'orientation': PropEntry(PropType.FLOAT,
                                 display_name="Rotation (°)",
                                 description="Clockwise rotation applied to the (horizontal) sine wave, set between -180° and +180°.",
                                 default_value=0.0,
                                 min_value=-180.0,
                                 max_value=180.0),
        'num_points': PropEntry(PropType.INT,
                                display_name="Line resolution",
                                description="Number of points used to draw the line, set between 2 and 500. The more points used, the more accurate the line is to a sine wave.",
                                default_value=100,
                                min_value=2,
                                max_value=500)
    }
)



class SineWaveNode(UnitNode):
    NAME = "Sine Wave"
    DEFAULT_NODE_INFO = DEF_SINE_WAVE_INFO

    @staticmethod
    def helper(amplitude, wavelength, centre_y, phase, x_min, x_max, stroke_width=1, num_points=100, orientation=0):
        return SineWave(amplitude, wavelength, centre_y, phase, x_min, x_max, stroke_width, num_points).rotate(
            orientation, (0.5, 0.5))

    def compute(self, output_port_key='_main'):
        try:
            sine_wave = SineWaveNode.helper(self._prop_val('amplitude'), self._prop_val('wavelength'),
                                            self._prop_val('centre_y'),
                                            self._prop_val('phase'), self._prop_val('x_min'),
                                            self._prop_val('x_max'),
                                            self._prop_val('stroke_width'), self._prop_val('num_points'),
                                            self._prop_val('orientation'))
        except ValueError as e:
            raise NodeInputException(str(e), self.uid)
        return sine_wave

    def visualise(self):
        group = Group(debug_info="Sine wave")
        group.add(self.compute())
        return group


DEF_CUSTOM_LINE_INFO = NodeInfo(
    description="Create a custom line by defining the points the line passes through. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    port_defs={
        (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Polyline)
    },
    prop_entries={
        'points': PropEntry(PropType.POINT_TABLE,
                            display_name="Points",
                            description="Points defining the path of the line (in order).",
                            default_value=[(0, 0), (0.5, 0.5), (1, 0)]),
        'stroke_width': PropEntry(PropType.FLOAT,
                                  display_name="Line thickness",
                                  description="Thickness of the line drawing.",
                                  default_value=1.0,
                                  min_value=0.0)
    }
)



class CustomLineNode(UnitNode):
    NAME = "Custom Line"
    DEFAULT_NODE_INFO = DEF_CUSTOM_LINE_INFO

    @staticmethod
    def helper(points, stroke='black', stroke_width=1):
        return Polyline(points, stroke, stroke_width)

    def compute(self, output_port_key='_main'):
        return CustomLineNode.helper(self._prop_val('points'), 'black', self._prop_val('stroke_width'))

    def visualise(self):
        group = Group(debug_info="Custom Line")
        group.add(self.compute())
        return group


DEF_STRAIGHT_LINE_NODE_INFO = NodeInfo(
    description="Create a straight line by defining the start and stop points. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    port_defs={
        (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Polyline)
    },
    prop_entries={
        'start_coord': PropEntry(PropType.COORDINATE,
                                 display_name="Start coordinate",
                                 description="Coordinate of the start of the line. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
                                 default_value=(1, 0)),
        'stop_coord': PropEntry(PropType.COORDINATE,
                                 display_name="Stop coordinate",
                                 description="Coordinate of the end of the line. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
                                 default_value=(0, 1)),
        'stroke_width': PropEntry(PropType.FLOAT,
                                  display_name="Line thickness",
                                  description="Thickness of the straight line.",
                                  default_value=1,
                                  min_value=0)
    }
)


class StraightLineNode(UnitNode):
    NAME = "Straight Line"
    DEFAULT_NODE_INFO = DEF_STRAIGHT_LINE_NODE_INFO

    @staticmethod
    def helper(start_coord, stop_coord, stroke='black', stroke_width=1):
        return Polyline([start_coord, stop_coord], stroke, stroke_width)

    def compute(self, out_port_key='_main'):
        return StraightLineNode.helper(self._prop_val('start_coord'), self._prop_val('stop_coord'), 'black',
                                       self._prop_val('stroke_width'))

    def visualise(self):
        group = Group(debug_info="Straight Line")
        group.add(self.compute())
        return group




DEF_POLYGON_INFO = NodeInfo(
    description="Create a polygon shape by defining the connecting points and deciding the fill colour. Optionally a gradient can be used to fill the shape. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    port_defs={(PortIO.INPUT, 'import_points'): PortDef("Import Points", PT_Polyline),
               (PortIO.INPUT, 'fill'): PortDef("Fill", PT_Fill, optional=True),
               (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Element)},
    prop_entries={'points': PropEntry(PropType.POINT_TABLE,
                                        display_name="Points",
                                        description="Points defining the path of the polygon edge (in order).",
                                        default_value=[(0, 0), (0, 1), (1, 1)]),
                    'fill': PropEntry(PropType.FILL,
                                      display_name="Fill",
                                      description="Polygon fill colour.",
                                      default_value=(0, 0, 0, 255)),
                    'stroke_width': PropEntry(PropType.FLOAT,
                                              display_name="Border thickness",
                                              description="Thickness of the line drawing the polygon border.",
                                              default_value=1,
                                              min_value=0)}
)

class PolygonNode(UnitNode):
    NAME = "Polygon"
    DEFAULT_NODE_INFO = DEF_POLYGON_INFO

    @staticmethod
    def helper(fill, points, stroke, stroke_width):
        if isinstance(fill, Gradient):
            fill_opacity = 255
        else:
            fill, fill_opacity = process_rgb(fill)
        return Polygon(points, fill, fill_opacity, stroke, stroke_width)

    def compute(self, out_port_key='_main'):
        # Process input polylines
        # handle_multi_inputs(self._input_node('import_points'), self.prop_vals['points'])
        return PolygonNode.helper(self._prop_val('fill'), self._prop_val('points'), 'none',
                                  self._prop_val('stroke_width'))

    def visualise(self):
        group = Group(debug_info="Polygon")
        group.add(self.compute())
        return group


DEF_RECTANGLE_NODE_INFO = NodeInfo(
    description="Create a rectangle shape by deciding the fill colour. Optionally a gradient can be used to fill the shape.",
    port_defs={(PortIO.INPUT, 'fill'): PortDef("Fill", PT_Fill),
               (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Element)},
    prop_entries={'fill': PropEntry(PropType.FILL,
                                      display_name="Fill",
                                      description="Rectangle fill colour.",
                                      default_value=(0, 0, 0, 255))}
)


class RectangleNode(UnitNode):
    NAME = "Rectangle"
    DEFAULT_NODE_INFO = DEF_RECTANGLE_NODE_INFO

    @staticmethod
    def helper(colour):
        return PolygonNode.helper(colour, [(0, 0), (0, 1), (1, 1), (1, 0)], 'none', 1)

    def compute(self, out_port_key='_main'):
        return RectangleNode.helper(self._prop_val('fill'))

    def visualise(self):
        group = Group(debug_info="Rectangle")
        group.add(self.compute())
        return group


DEF_ELLIPSE_INFO = NodeInfo(
    description="Create an ellipse shape. A gradient can be used to fill the shape if required. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    port_defs={
        (PortIO.INPUT, 'fill'): PortDef("Colour", PT_Fill, optional=True),
        (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Ellipse)
    },
    prop_entries={
        'rx': PropEntry(PropType.FLOAT,
                        display_name="Horizontal radius (rx)",
                        description="Horizontal semi-axis of the ellipse. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
                        default_value=0.5,
                        min_value=0.0),
        'ry': PropEntry(PropType.FLOAT,
                        display_name="Vertical radius (ry)",
                        description="Vertical semi-axis of the ellipse. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
                        default_value=0.5,
                        min_value=0.0),
        'centre': PropEntry(PropType.COORDINATE,
                            display_name="Centre coordinate",
                            description="Coordinate of the ellipse centre. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
                            default_value=(0.5, 0.5)),
        'fill': PropEntry(PropType.FILL,
                          display_name="Colour",
                          description="Ellipse fill colour.",
                          default_value=(0, 0, 0, 255)),
        'stroke_width': PropEntry(PropType.FLOAT,
                                  display_name="Border thickness",
                                  description="Thickness of the line drawing the ellipse border.",
                                  default_value=1.0,
                                  min_value=0.0)
    }
)



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

    def compute(self, output_port_key='_main'):
        return EllipseNode.helper(self._prop_val('fill'), self._prop_val('centre'),
                                  (self._prop_val('rx'), self._prop_val('ry')),
                                  'none', self._prop_val('stroke_width'))

    def visualise(self):
        group = Group(debug_info="Ellipse")
        group.add(self.compute())
        return group


DEF_CIRCLE_INFO = NodeInfo(
    description="Create a circle shape. A gradient can be used to fill the shape if required. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    port_defs={
        (PortIO.INPUT, 'fill'): PortDef("Colour", PT_Fill, optional=True),
        (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Ellipse)
    },
    prop_entries={
        'r': PropEntry(PropType.FLOAT,
                       display_name="Radius",
                       description="Radius of the circle. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
                       default_value=0.5,
                       min_value=0.0),
        'centre': PropEntry(PropType.COORDINATE,
                            display_name="Centre coordinate",
                            description="Coordinate of the circle centre. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
                            default_value=(0.5, 0.5)),
        'fill': PropEntry(PropType.FILL,
                          display_name="Colour",
                          description="Circle fill colour.",
                          default_value=(0, 0, 0, 255)),
        'stroke_width': PropEntry(PropType.FLOAT,
                                  display_name="Border thickness",
                                  description="Thickness of the line drawing the circle border.",
                                  default_value=1.0,
                                  min_value=0.0)
    }
)



class CircleNode(UnitNode):
    NAME = "Circle"
    DEFAULT_NODE_INFO = DEF_CIRCLE_INFO

    @staticmethod
    def helper(colour, centre, radius, stroke='none', stroke_width=1):
        return EllipseNode.helper(colour, centre, (radius, radius), stroke, stroke_width)

    def compute(self, output_port_key='_main'):
        return CircleNode.helper(self._prop_val('fill'),
                                 self._prop_val('centre'),
                                 self._prop_val('r'),
                                 'none',
                                 self._prop_val('stroke_width'))

    def visualise(self):
        group = Group(debug_info="Circle")
        group.add(self.compute())
        return group


class ShapeNode(CombinationNode):
    NAME = "Shape"
    SELECTIONS = [PolygonNode, RectangleNode, EllipseNode, CircleNode, SineWaveNode, CustomLineNode, StraightLineNode]
