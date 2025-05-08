# from ui_old.nodes.gradient_datatype import Gradient
# from ui_old.nodes.multi_input_handler import handle_multi_inputs
# from ui_old.nodes.node_input_exception import NodeInputException
# from ui_old.nodes.nodes import UnitNode, PropType, PropTypeList, CombinationNode, UnitNodeInfo
# from ui_old.nodes.shape_datatypes import Polygon, Ellipse, SineWave, Polyline, Group
# from ui_old.nodes.utils import process_rgb
# from ui_old.port_defs import PortDef, PT_Element, PT_Polyline, PT_Ellipse, PT_Fill
#
# SINE_WAVE_NODE_INFO = UnitNodeInfo(
#     name="Sine Wave",
#     out_port_defs=[PortDef("Drawing", PT_Polyline)],
#     prop_type_list=PropTypeList(
#         [
#             PropType("amplitude", "float", default_value=0.5,
#                      description="Amplitude of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
#                      display_name="Amplitude"),
#             PropType("wavelength", "float", default_value=1.0, min_value=0.01,
#                      description="Wavelength of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
#                      display_name="Wavelength"),
#             PropType("centre_y", "float", default_value=0.5,
#                      description="Equilibrium position of the sine wave. With 0° rotation, this is the y-coordinate of the equilibrium position. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
#                      display_name="Equilibrium position"),
#             PropType("phase", "float", default_value=0.0,
#                      description="Phase of the sine wave in degrees.", display_name="Phase (°)"),
#             PropType("x_min", "float", default_value=0.0,
#                      description="Start position of the sine wave. With 0° rotation, this is the x-coordinate of the start of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
#                      display_name="Wave start"),
#             PropType("x_max", "float", default_value=1.0,
#                      description="Stop position of the sine wave. With 0° rotation, this is the x-coordinate of the end of the sine wave. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
#                      display_name="Wave stop"),
#             PropType("stroke_width", "float", default_value=1.0,
#                      description="Thickness of the line drawing the sine wave.", display_name="Line thickness",
#                      min_value=0.0),
#             PropType("orientation", "float", default_value=0.0,
#                      description="Clockwise rotation applied to the (horizontal) sine wave, set between -180° and +180°.",
#                      display_name="Rotation (°)", min_value=-180.0, max_value=180.0),
#             PropType("num_points", "int", default_value=100,
#                      description="Number of points used to draw the line, set between 2 and 500. The more points used, the more accurate the line is to a sine wave.",
#                      min_value=2, max_value=500, display_name="Line resolution")
#         ]
#     ),
#     description="Create part of a sine wave, defining properties such as the amplitude and wavelength. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner."
# )
#
#
# class SineWaveNode(UnitNode):
#     UNIT_NODE_INFO = SINE_WAVE_NODE_INFO
#
#     @staticmethod
#     def helper(amplitude, wavelength, centre_y, phase, x_min, x_max, stroke_width=1, num_points=100, orientation=0):
#         return SineWave(amplitude, wavelength, centre_y, phase, x_min, x_max, stroke_width, num_points).rotate(
#             orientation, (0.5, 0.5))
#
#     def compute(self):
#         try:
#             sine_wave = SineWaveNode.helper(self.get_prop_val('amplitude'), self.get_prop_val('wavelength'),
#                                             self.get_prop_val('centre_y'),
#                                             self.get_prop_val('phase'), self.get_prop_val('x_min'),
#                                             self.get_prop_val('x_max'),
#                                             self.get_prop_val('stroke_width'), self.get_prop_val('num_points'),
#                                             self.get_prop_val('orientation'))
#         except ValueError as e:
#             raise NodeInputException(str(e), self.node_id)
#         return sine_wave
#
#     def visualise(self):
#         group = Group(debug_info="Sine wave")
#         group.add(self.compute())
#         return group
#
#
# CUSTOM_LINE_NODE_INFO = UnitNodeInfo(
#     name="Custom Line",
#     out_port_defs=[PortDef("Drawing", PT_Polyline)],
#     prop_type_list=PropTypeList(
#         [
#             PropType("points", "point_table", default_value=[(1, 0), (0, 1)],
#                      description="Points defining the path of the line (in order).", display_name="Points"),
#             PropType("stroke_width", "float", default_value=1.0,
#                      description="Thickness of the line drawing.", display_name="Line thickness", min_value=0.0)
#         ]
#     ),
#     description="Create a custom line by defining the points the line passes through. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner."
# )
#
#
# class CustomLineNode(UnitNode):
#     UNIT_NODE_INFO = CUSTOM_LINE_NODE_INFO
#
#     @staticmethod
#     def helper(points, stroke='black', stroke_width=1):
#         return Polyline(points, stroke, stroke_width)
#
#     def compute(self):
#         return CustomLineNode.helper(self.get_prop_val('points'), 'black', self.get_prop_val('stroke_width'))
#
#     def visualise(self):
#         group = Group(debug_info="Custom Line")
#         group.add(self.compute())
#         return group
#
#
# STRAIGHT_LINE_NODE_INFO = UnitNodeInfo(
#     name="Straight Line",
#     out_port_defs=[PortDef("Drawing", PT_Polyline)],
#     prop_type_list=PropTypeList(
#         [
#             PropType("start_coord", "coordinate", default_value=(1, 0),
#                      description="Coordinate of the start of the line. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
#                      display_name="Start coordinate"),
#             PropType("stop_coord", "coordinate", default_value=(0, 1),
#                      description="Coordinate of the end of the line. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
#                      display_name="Stop coordinate"),
#             PropType("stroke_width", "float", default_value=1.0,
#                      description="Thickness of the straight line.", display_name="Line thickness", min_value=0.0)
#         ]
#     ),
#     description="Create a straight line by defining the start and stop points. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner."
# )
#
#
# class StraightLineNode(UnitNode):
#     UNIT_NODE_INFO = STRAIGHT_LINE_NODE_INFO
#
#     @staticmethod
#     def helper(start_coord, stop_coord, stroke='black', stroke_width=1):
#         return Polyline([start_coord, stop_coord], stroke, stroke_width)
#
#     def compute(self):
#         return StraightLineNode.helper(self.get_prop_val('start_coord'), self.get_prop_val('stop_coord'), 'black',
#                                        self.get_prop_val('stroke_width'))
#
#     def visualise(self):
#         group = Group(debug_info="Straight Line")
#         group.add(self.compute())
#         return group
#
#
from ui.nodes.gradient_datatype import Gradient
from ui.nodes.node_defs import NodeInfo, PropType, PropEntry
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Polyline, PT_Fill, PT_Element
from ui.nodes.shape_datatypes import Polygon, Group
from ui.nodes.utils import process_rgb

DEF_POLYGON_INFO = NodeInfo(
    description="Create a polygon shape by defining the connecting points and deciding the fill colour. Optionally a gradient can be used to fill the shape. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
    port_defs={(PortIO.INPUT, 'import_points'): PortDef("Import Points", PT_Polyline),
               (PortIO.INPUT, 'fill'): PortDef("Fill", PT_Fill),
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
#
#
# RECTANGLE_NODE_INFO = UnitNodeInfo(
#     name="Rectangle",
#     prop_port_defs=[PortDef('Colour', PT_Fill, key_name='fill')],
#     out_port_defs=[PortDef("Drawing", PT_Element)],
#     prop_type_list=PropTypeList(
#         [
#             PropType("fill", "colour", default_value=(0, 0, 0, 255),
#                      description="Rectangle fill colour.", display_name="Colour", port_modifiable=True)
#         ]
#     ),
#     description="Create a rectangle shape by deciding the fill colour. Optionally a gradient can be used to fill the shape."
# )
#
#
# class RectangleNode(UnitNode):
#     UNIT_NODE_INFO = RECTANGLE_NODE_INFO
#
#     @staticmethod
#     def helper(colour):
#         return PolygonNode.helper(colour, [(0, 0), (0, 1), (1, 1), (1, 0)], 'none', 1)
#
#     def compute(self):
#         return RectangleNode.helper(self.get_prop_val('fill'))
#
#     def visualise(self):
#         group = Group(debug_info="Rectangle")
#         group.add(self.compute())
#         return group
#
#
# ELLIPSE_NODE_INFO = UnitNodeInfo(
#     name="Ellipse",
#     prop_port_defs=[PortDef('Colour', PT_Fill, key_name='fill')],
#     out_port_defs=[PortDef("Drawing", PT_Ellipse)],
#     prop_type_list=PropTypeList(
#         [
#             PropType("rx", "float", default_value=0.5, min_value=0.0,
#                      description="Horizontal semi-axis of the ellipse. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
#                      display_name="Horizontal radius (rx)"),
#             PropType("ry", "float", default_value=0.5, min_value=0.0,
#                      description="Vertical semi-axis of the ellipse. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
#                      display_name="Vertical radius (ry)"),
#             PropType("centre", "coordinate", default_value=(0.5, 0.5),
#                      description="Coordinate of the ellipse centre. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
#                      display_name="Centre coordinate"),
#             PropType("fill", "colour", default_value=(0, 0, 0, 255),
#                      description="Ellipse fill colour.", display_name="Colour", port_modifiable=True),
#             PropType("stroke_width", "float", default_value=1.0,
#                      description="Thickness of the line drawing the ellipse border.", display_name="Border thickness",
#                      min_value=0.0)
#         ]
#     ),
#     description="Create an ellipse shape. A gradient can be used to fill the shape if required. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner."
# )
#
#
# class EllipseNode(UnitNode):
#     UNIT_NODE_INFO = ELLIPSE_NODE_INFO
#
#     @staticmethod
#     def helper(colour, centre, radius, stroke='none', stroke_width=1):
#         if isinstance(colour, Gradient):
#             fill = colour
#             fill_opacity = 255
#         else:
#             fill, fill_opacity = process_rgb(colour)
#         return Ellipse(centre, radius, fill,
#                        fill_opacity, stroke, stroke_width)
#
#     def compute(self):
#         return EllipseNode.helper(self.get_prop_val('fill'), self.get_prop_val('centre'),
#                                   (self.get_prop_val('rx'), self.get_prop_val('ry')),
#                                   'none', self.get_prop_val('stroke_width'))
#
#     def visualise(self):
#         group = Group(debug_info="Ellipse")
#         group.add(self.compute())
#         return group
#
#
# CIRCLE_NODE_INFO = UnitNodeInfo(
#     name="Circle",
#     prop_port_defs=[PortDef('Colour', PT_Fill, key_name='fill')],
#     out_port_defs=[PortDef("Drawing", PT_Ellipse)],
#     prop_type_list=PropTypeList(
#         [
#             PropType("r", "float", default_value=0.5, min_value=0.0,
#                      description="Radius of the circle. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
#                      display_name="Radius"),
#             PropType("centre", "coordinate", default_value=(0.5, 0.5),
#                      description="Coordinate of the circle centre. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner.",
#                      display_name="Centre coordinate"),
#             PropType("fill", "colour", default_value=(0, 0, 0, 255),
#                      description="Circle fill colour.", display_name="Colour", port_modifiable=True),
#             PropType("stroke_width", "float", default_value=1.0,
#                      description="Thickness of the line drawing the circle border.", display_name="Border thickness",
#                      min_value=0.0)
#         ]
#     ),
#     description="Create a circle shape. A gradient can be used to fill the shape if required. Coordinates are set in the context of a 1x1 canvas, with (0.5, 0.5) being the centre and (0,0) being the top-left corner."
# )
#
#
# class CircleNode(UnitNode):
#     UNIT_NODE_INFO = CIRCLE_NODE_INFO
#
#     @staticmethod
#     def helper(colour, centre, radius, stroke='none', stroke_width=1):
#         return EllipseNode.helper(colour, centre, (radius, radius), stroke, stroke_width)
#
#     def compute(self):
#         return CircleNode.helper(self.get_prop_val('fill'),
#                                  self.get_prop_val('centre'),
#                                  self.get_prop_val('r'),
#                                  'none',
#                                  self.get_prop_val('stroke_width'))
#
#     def visualise(self):
#         group = Group(debug_info="Circle")
#         group.add(self.compute())
#         return group
#
#
# class ShapeNode(CombinationNode):
#     NAME = "Shape"
#     SELECTIONS = [PolygonNode, RectangleNode, EllipseNode, CircleNode, SineWaveNode, CustomLineNode, StraightLineNode]
