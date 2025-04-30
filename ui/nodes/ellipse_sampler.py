import math

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNodeInfo, PropTypeList, PropType, UnitNode
from ui.nodes.shape import EllipseNode
from ui.nodes.shape_datatypes import Ellipse, Group
from ui.nodes.utils import process_rgb
from ui.port_defs import PortDef, PortType, PT_Ellipse, PT_NumberList, PT_PointList

ELLIPSE_SAMPLER_NODE_INFO = UnitNodeInfo(
    name="Ellipse Sampler",
    resizable=True,
    selectable=False,
    in_port_defs=[PortDef("Ellipse", PT_Ellipse, key_name='ellipse')],
    out_port_defs=[PortDef("Samples", PT_PointList)],
    prop_type_list=PropTypeList(
        [
            PropType("start_angle", "float", default_value=0,
                     description="Central angle (in degrees) of the first sample (point along the edge of the ellipse) with the ellipse's right-most point. The angle is measured clockwise. At 0° the first sample is at its right-most point. At 90° the first sample is at the bottom-most point.", display_name="Angle of first sample (°)"),
            PropType("num_samples", "int", default_value=5,
                     description="Number of samples (points along the edge of the ellipse), at most 1.", min_value=1, display_name="Sample number")
        ]
    ),
    description="Sample (angularly) equally-spaced points along the edge of an ellipse or circle."
)


class EllipseSamplerNode(UnitNode):
    UNIT_NODE_INFO = ELLIPSE_SAMPLER_NODE_INFO

    @staticmethod
    def angle_to_point(angle_rad, ellipse):
        x = ellipse.center[0] + ellipse.r[0] * math.cos(angle_rad)
        y = ellipse.center[1] + ellipse.r[1] * math.sin(angle_rad)
        return x, y

    @staticmethod
    def helper(element, start_angle, num_samples):
        if element:
            ellipse = element[0]
            assert isinstance(ellipse, Ellipse)
            samples = []
            angle = math.radians(start_angle)
            step = 2 * math.pi / num_samples
            for _ in range(num_samples):
                samples.append(EllipseSamplerNode.angle_to_point(angle, ellipse))
                angle += step
            return samples

    def compute(self):
        element = self.get_input_node('ellipse').compute()
        return EllipseSamplerNode.helper(element, self.get_prop_val('start_angle'), self.get_prop_val('num_samples'))

    def visualise(self, temp_dir, height, wh_ratio):
        points = self.compute()
        if points:
            ret_element = Group()
            for p in points:
                ret_element.add(Ellipse(p, (0.01, 0.01), 'black', 255, 'black', 0))
            return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (ret_element, None)).save()