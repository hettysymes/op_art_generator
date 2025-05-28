import math

from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus
from nodes.nodes import UnitNode
from nodes.prop_types import PT_Ellipse, PT_Float, PT_Int, PT_Point
from nodes.prop_values import List, Int, Float, Point
from nodes.shape_datatypes import Ellipse

DEF_ELLIPSE_SAMPLER_INFO = PrivateNodeInfo(
    description="Sample (angularly) equally-spaced points along the edge of an ellipse or circle.",
    prop_defs={
        'ellipse': PropDef(
            prop_type=PT_Ellipse(),
            display_name="Ellipse",
            input_port_status=PortStatus.COMPULSORY
        ),
        'start_angle': PropDef(
            prop_type=PT_Float(),
            display_name="Angle of first sample (°)",
            description=(
                "Central angle (in degrees) of the first sample (point along the edge of the ellipse) with the ellipse's "
                "right-most point. The angle is measured clockwise. At 0° the first sample is at its right-most point. "
                "At 90° the first sample is at the bottom-most point."
            ),
            default_value=Float(0)
        ),
        'num_samples': PropDef(
            prop_type=PT_Int(min_value=1),
            display_name="Sample number",
            description="Number of samples (points along the edge of the ellipse), at most 1.",
            default_value=Int(5)
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="Samples",
            display_in_props=False
        )
    }
)


class EllipseSamplerNode(UnitNode):
    NAME = "Ellipse Sampler"
    DEFAULT_NODE_INFO = DEF_ELLIPSE_SAMPLER_INFO

    @staticmethod
    def angle_to_point(angle_rad: float, centre: tuple[float, float], radius: tuple[float, float]) -> Point:
        x = centre[0] + radius[0] * math.cos(angle_rad)
        y = centre[1] + radius[1] * math.sin(angle_rad)
        return Point(x, y)

    @staticmethod
    def helper(centre: tuple[float, float], radius: tuple[float, float], start_angle: float, num_samples: int) -> List[PT_Point]:
        samples = List(PT_Point())
        angle = math.radians(start_angle)
        step = 2 * math.pi / num_samples
        for _ in range(num_samples):
            samples.append(EllipseSamplerNode.angle_to_point(angle, centre, radius))
            angle += step
        return samples

    def compute(self, props: ResolvedProps, *args):
        ellipse: Ellipse = props.get('ellipse')
        if ellipse is None:
            return {}
        return {'_main': EllipseSamplerNode.helper(ellipse.center, ellipse.r, props.get('start_angle'),
                                                   props.get('num_samples'))}
