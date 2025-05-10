from ui.nodes.node_defs import NodeInfo
from ui.nodes.node_implementations.ellipse_sampler import EllipseSamplerNode
from ui.nodes.node_implementations.port_ref_table_handler import handle_port_ref_table
from ui.nodes.nodes import UnitNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Element, PT_Ellipse, PT_List, PT_Fill, PT_Float, PT_Int, PropEntry
from ui.nodes.shape_datatypes import Group, Polygon
from ui.nodes.utils import process_rgb

DEF_BLAZE_MAKER_INFO = NodeInfo(
    description="Input 2+ circle/ellipse shapes to create an image similar to those in the Blaze series by Bridget Riley.",
    port_defs={
        (PortIO.INPUT, 'ellipses'): PortDef("Input Ellipses", PT_List(PT_Ellipse())),
        (PortIO.OUTPUT, '_main'): PortDef("Drawing", PT_Element())
    },
    prop_entries={
        'num_polygons': PropEntry(PT_Int(min_value=1),
                                  display_name="Zig-zag number",
                                  description="Number of zig-zags, at most 1.",
                                  default_value=36),
        'angle_diff': PropEntry(PT_Float(),
                                display_name="Zig-zag angle (°)",
                                description="Angle (in degrees) determining the sharpness and direction of the zig-zags. Angles with a higher magnitude give sharper zig-zags. Negative angles give zig-zags in the reverse direction to positive angles.",
                                default_value=20),
        'fill': PropEntry(PT_Fill(),
                          display_name="Zig-zag colour",
                          description="Zig-zag colour.",
                          default_value=(0, 0, 0, 255))
    }
)


class BlazeMakerNode(UnitNode):
    NAME = "Blaze Maker"
    DEFAULT_NODE_INFO = DEF_BLAZE_MAKER_INFO

    @staticmethod
    def helper(num_polygons, ellipses, angle_diff, colour):
        num_samples = num_polygons * 2
        ret_group = Group(debug_info="Blaze Maker")
        # Sort ellipses in order of ascending radius
        ellipses.sort(key=lambda ellipse: ellipse.r[0] ** 2 + ellipse.r[1] ** 2)
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

    def compute(self, out_port_key='_main'):
        if self._prop_val('ellipses'):
            return BlazeMakerNode.helper(self._prop_val('num_polygons'), self._prop_val('ellipses'),
                                         self._prop_val('angle_diff'), self._prop_val('fill'))
        return None
