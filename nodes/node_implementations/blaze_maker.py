from nodes.node_defs import PrivateNodeInfo, PropDef, PortStatus, ResolvedProps
from nodes.node_implementations.ellipse_sampler import EllipseSamplerNode
from nodes.nodes import UnitNode
from nodes.prop_types import PT_BlazeCircleDef, PT_List, PT_Int, PT_Float, PT_Colour
from nodes.prop_values import List, Int, Float, Colour
from nodes.shape_datatypes import Group

DEF_BLAZE_MAKER_INFO = PrivateNodeInfo(
    description="Create an image similar to those in the Blaze series by Bridget Riley.",
    prop_defs={
        'circle_defs': PropDef(
            prop_type=PT_List(PT_BlazeCircleDef()),
            display_name="Circle definitions",
            description="Circle definitions in the Blaze image, defined by a centre offset and radius.",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN,
            default_value=List(PT_BlazeCircleDef())
        ),
        'num_polygons': PropDef(
            prop_type=PT_Int(min_value=1),
            display_name="Zig-zag number",
            description="Number of zig-zags, at most 1.",
            default_value=Int(36)
        ),
        'angle_diff': PropDef(
            prop_type=PT_Float(),
            display_name="Zig-zag angle (°)",
            description="Angle (in degrees) determining the sharpness and direction of the zig-zags. Angles with a higher magnitude give sharper zig-zags. Negative angles give zig-zags in the reverse direction to positive angles.",
            default_value=Float(20)
        ),
        'colour': PropDef(
            prop_type=PT_Colour(),
            display_name="Zig-zag colour",
            description="Zig-zag colour.",
            default_value=Colour(0, 0, 0, 255)
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Drawing",
            display_in_props=False
        )
    }
)

class BlazeMakerNode(UnitNode):
    NAME = "Blaze Maker"
    DEFAULT_NODE_INFO = DEF_BLAZE_MAKER_INFO


    def compute(self, props: ResolvedProps, *args):
        circle_defs: List[PT_BlazeCircleDef] = props.get('circle_defs')
        num_samples: float = props.get('num_polygons') * 2
        ret_group = Group(debug_info="Blaze Maker")

        start_angle = 0
        samples_list = []
        for ellipse in ellipses:
            start_angle += angle_diff
            angle_diff *= -1
            samples_list.append(EllipseSamplerNode.helper(ellipse, start_angle, num_samples))
        # Obtain lines
        lines = [[] for _ in range(num_samples)]
        for samples in samples_list:
            for i, sample in enumerate(samples):
                lines[i].append(sample)
        # Draw polygons
        fill, fill_opacity = process_rgb(colour)
        for i in range(0, len(lines), 2):
            points = lines[i - 1] + list(reversed(lines[i]))
            ret_group.add(Polygon(points, fill, fill_opacity))
        return ret_group


# class BlazeMakerNode(UnitNode):
#     NAME = "Blaze Maker"
#     DEFAULT_NODE_INFO = DEF_BLAZE_MAKER_INFO
#
#     @staticmethod
#     def helper(num_polygons, ellipses, angle_diff, colour):
#         num_samples = num_polygons * 2
#         ret_group = Group(debug_info="Blaze Maker")
#         # Sort ellipses in order of ascending radius
#         ellipses.sort(key=lambda ellipse: ellipse.r[0] ** 2 + ellipse.r[1] ** 2)
#         start_angle = 0
#         samples_list = []
#         for ellipse in ellipses:
#             start_angle += angle_diff
#             angle_diff *= -1
#             samples_list.append(EllipseSamplerNode.helper(ellipse, start_angle, num_samples))
#         # Obtain lines
#         lines = [[] for _ in range(num_samples)]
#         for samples in samples_list:
#             for i, sample in enumerate(samples):
#                 lines[i].append(sample)
#         # Draw polygons
#         fill, fill_opacity = process_rgb(colour)
#         for i in range(0, len(lines), 2):
#             points = lines[i - 1] + list(reversed(lines[i]))
#             ret_group.add(Polygon(points, fill, fill_opacity))
#         return ret_group
#
#     def compute(self):
#         if self._prop_val('ellipses'):
#             self.set_compute_result(BlazeMakerNode.helper(self._prop_val('num_polygons'), self._prop_val('ellipses'),
#                                                           self._prop_val('angle_diff'), self._prop_val('fill')))
