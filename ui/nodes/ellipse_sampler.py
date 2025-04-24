import math

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNodeInfo, PropTypeList, PropType, UnitNode
from ui.nodes.shape import EllipseNode
from ui.nodes.shape_datatypes import Ellipse, Element
from ui.nodes.utils import process_rgb
from ui.port_defs import PortDef, PortType

ELLIPSE_SAMPLER_NODE_INFO = UnitNodeInfo(
    name="Ellipse Sampler",
    resizable=True,
    selectable=False,
    in_port_defs=[PortDef("Ellipse", PortType.ELEMENT)],
    out_port_defs=[PortDef("Samples", PortType.VALUE_LIST)],
    prop_type_list=PropTypeList(
        [
            PropType("start_angle", "float", default_value=0,
                     description="", display_name="start angle", min_value=-360, max_value=360),
            PropType("num_samples", "int", default_value=5,
                     description="", min_value=1, display_name="number of samples")
        ]
    )
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
        element = self.input_nodes[0].compute()
        return EllipseSamplerNode.helper(element, self.prop_vals['start_angle'], self.prop_vals['num_samples'])

    def visualise(self, height, wh_ratio):
        points = self.compute()
        if points:
            ret_element = Element()
            for p in points:
                ret_element.add(Ellipse(p, (0.01, 0.01), 'black', 255, 'black', 0))
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (ret_element, None)).save()