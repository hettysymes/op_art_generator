import math

from ui.nodes.node_defs import NodeInfo
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Ellipse, PT_Point, PT_List
from ui.nodes.prop_defs import PrT_Float, PrT_Int, PropEntry
from ui.nodes.shape_datatypes import Ellipse, Group

DEF_ELLIPSE_SAMPLER_INFO = NodeInfo(
    description="Sample (angularly) equally-spaced points along the edge of an ellipse or circle.",
    port_defs={
        (PortIO.INPUT, 'ellipse'): PortDef("Ellipse", PT_Ellipse()),
        (PortIO.OUTPUT, '_main'): PortDef("Samples", PT_List(PT_Point()))
    },
    prop_entries={
        'start_angle': PropEntry(PrT_Float(),
                                 display_name="Angle of first sample (°)",
                                 description="Central angle (in degrees) of the first sample (point along the edge of the ellipse) with the ellipse's right-most point. The angle is measured clockwise. At 0° the first sample is at its right-most point. At 90° the first sample is at the bottom-most point.",
                                 default_value=0),
        'num_samples': PropEntry(PrT_Int(),
                                 display_name="Sample number",
                                 description="Number of samples (points along the edge of the ellipse), at most 1.",
                                 default_value=5,
                                 min_value=1)
    }
)


class EllipseSamplerNode(UnitNode):
    NAME = "Ellipse Sampler"
    DEFAULT_NODE_INFO = DEF_ELLIPSE_SAMPLER_INFO

    @staticmethod
    def angle_to_point(angle_rad, ellipse):
        x = ellipse.center[0] + ellipse.r[0] * math.cos(angle_rad)
        y = ellipse.center[1] + ellipse.r[1] * math.sin(angle_rad)
        return x, y

    @staticmethod
    def helper(ellipse, start_angle, num_samples):
        assert isinstance(ellipse, Ellipse)
        samples = []
        angle = math.radians(start_angle)
        step = 2 * math.pi / num_samples
        for _ in range(num_samples):
            samples.append(EllipseSamplerNode.angle_to_point(angle, ellipse))
            angle += step
        return samples

    def compute(self, out_port_key='_main'):
        ellipse = self._prop_val('ellipse')
        if ellipse:
            return EllipseSamplerNode.helper(ellipse, self._prop_val('start_angle'),
                                             self._prop_val('num_samples'))
        return None

    def visualise(self):
        points = self.compute()
        if points:
            ret_group = Group(debug_info="Ellipse Sampler")
            for p in points:
                ret_group.add(Ellipse(p, (0.01, 0.01), 'black', 255, 'black', 0))
            return ret_group
        return None
