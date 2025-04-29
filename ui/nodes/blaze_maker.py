from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.elem_ref import ElemRef
from ui.nodes.ellipse_sampler import EllipseSamplerNode
from ui.nodes.multi_input_handler import handle_multi_inputs
from ui.nodes.nodes import UnitNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.shape_datatypes import Element, Polyline, Polygon
from ui.nodes.utils import process_rgb
from ui.port_defs import PortType, PortDef, PT_Ellipse, PT_Element

BLAZE_MAKER_NODE_INFO = UnitNodeInfo(
    name="Blaze Maker",
    resizable=True,
    selectable=True,
    in_port_defs=[
        PortDef("Input Ellipses", PT_Ellipse, input_multiple=True, key_name='ellipses')
    ],
    out_port_defs=[PortDef("Drawing", PT_Element)],
    prop_type_list=PropTypeList([
        PropType("num_polygons", "int", default_value=36,
                 description="Number of zig-zags, at most 1.", min_value=1, display_name="Zig-zag number"),
        PropType("angle_diff", "float", default_value=20,
                         description="Angle (in degrees) determining the sharpness and direction of the zig-zags. Angles with a higher magnitude give sharper zig-zags. Negative angles give zig-zags in the reverse direction to positive angles.", display_name="Zig-zag angle (°)"),
        PropType("fill", "colour", default_value=(0, 0, 0, 255),
                 description="Zig-zag colour.", display_name="Zig-zag colour"),
        PropType("ellipses", "hidden", default_value=[],
                             description="")
    ]),
    description="Input 2+ circle/ellipse shapes to create an image similar to those in the Blaze series by Bridget Riley."
)


class BlazeMakerNode(UnitNode):
    UNIT_NODE_INFO = BLAZE_MAKER_NODE_INFO

    def compute(self):
        input_nodes = self.get_input_node('ellipses')
        handle_multi_inputs(input_nodes, self.prop_vals['ellipses'])
        # Return element
        if input_nodes:
            num_samples = self.get_prop_val('num_polygons')*2
            ret_elem = Element()
            ellipse_elems = [elem_ref.compute() for elem_ref in self.get_prop_val('ellipses')]
            # Sort ellipses in order of ascending radius
            ellipse_elems.sort(key=lambda elem: elem[0].r[0]**2 + elem[0].r[1]**2)
            start_angle = 0
            angle_diff = self.get_prop_val('angle_diff')
            samples_list = []
            for elem in ellipse_elems:
                start_angle += angle_diff
                angle_diff *= -1
                samples_list.append(EllipseSamplerNode.helper(elem, start_angle, num_samples))
            # Obtain lines
            lines = [[] for _ in range(num_samples)]
            for samples in samples_list:
                for i, sample in enumerate(samples):
                    lines[i].append(sample)
            # Draw polygons
            fill, fill_opacity = process_rgb(self.get_prop_val('fill'))
            for i in range(0, len(lines), 2):
                points = lines[i - 1] + list(reversed(lines[i]))
                ret_elem.add(Polygon(points, fill, fill_opacity))
            return ret_elem

    def visualise(self, temp_dir, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(self._return_path(temp_dir), height, wh_ratio, (element, None)).save()
