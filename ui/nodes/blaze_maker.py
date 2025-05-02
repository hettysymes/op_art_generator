from ui.nodes.ellipse_sampler import EllipseSamplerNode
from ui.nodes.multi_input_handler import handle_multi_inputs
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape_datatypes import Group, Polygon
from ui.nodes.utils import process_rgb
from ui.port_defs import PortDef, PT_Ellipse, PT_Element

BLAZE_MAKER_NODE_INFO = UnitNodeInfo(
    name="Blaze Maker",
    in_port_defs=[
        PortDef("Input Ellipses", PT_Ellipse, input_multiple=True, key_name='ellipses')
    ],
    out_port_defs=[PortDef("Drawing", PT_Element)],
    prop_type_list=PropTypeList([
        PropType("num_polygons", "int", default_value=36,
                 description="Number of zig-zags, at most 1.", min_value=1, display_name="Zig-zag number"),
        PropType("angle_diff", "float", default_value=20,
                 description="Angle (in degrees) determining the sharpness and direction of the zig-zags. Angles with a higher magnitude give sharper zig-zags. Negative angles give zig-zags in the reverse direction to positive angles.",
                 display_name="Zig-zag angle (°)"),
        PropType("fill", "colour", default_value=(0, 0, 0, 255),
                 description="Zig-zag colour.", display_name="Zig-zag colour"),
        PropType("ellipses", "hidden", default_value=[],
                 description="")
    ]),
    description="Input 2+ circle/ellipse shapes to create an image similar to those in the Blaze series by Bridget Riley."
)


class BlazeMakerNode(UnitNode):
    UNIT_NODE_INFO = BLAZE_MAKER_NODE_INFO

    @staticmethod
    def helper(num_polygons, ellipse_elem_refs, angle_diff, colour):
        num_samples = num_polygons * 2
        ret_group = Group(debug_info="Blaze Maker")
        ellipses = [elem_ref.compute() for elem_ref in ellipse_elem_refs]
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

    def compute(self):
        input_nodes = self.get_input_node('ellipses')
        handle_multi_inputs(input_nodes, self.prop_vals['ellipses'])
        if input_nodes:
            return BlazeMakerNode.helper(self.get_prop_val('num_polygons'), self.get_prop_val('ellipses'),
                                         self.get_prop_val('angle_diff'), self.get_prop_val('fill'))
        return None
