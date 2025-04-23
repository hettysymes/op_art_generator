import uuid

from cairosvg.shapes import polyline
from numpy.ma.core import indices

from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.nodes import UnitNode, PropType, PropTypeList, CombinationNode, UnitNodeInfo
from ui.nodes.point_ref import PointRef
from ui.nodes.shape_datatypes import Element, Polygon, Ellipse, SineWave, Shape
from ui.nodes.utils import process_rgb, rev_process_rgb
from ui.port_defs import PortDef, PortType

SINE_WAVE_NODE_INFO = UnitNodeInfo(
    name="Sine Wave",
    resizable=True,
    selectable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList(
        [
            PropType("amplitude", "float", default_value=0.5,
                     description=""),
            PropType("wavelength", "float", default_value=1.0,
                     description=""),
            PropType("centre_y", "float", default_value=0.5,
                     description=""),
            PropType("phase", "float", default_value=0.0,
                     description="", min_value=-360, max_value=360),
            PropType("x_min", "float", default_value=0.0,
                     description=""),
            PropType("x_max", "float", default_value=1.0,
                     description=""),
            PropType("stroke_width", "float", default_value=1.0,
                     description="", min_value=0.0),
            PropType("orientation", "float", default_value=0.0,
                     description="", min_value=-360.0, max_value=360.0),
            PropType("num_points", "int", default_value=100,
                     description="", min_value=2, max_value=500, display_name="line resolution")
        ]
    )
)


class SineWaveNode(UnitNode):
    UNIT_NODE_INFO = SINE_WAVE_NODE_INFO

    def compute(self):
        return Element([SineWave(self.prop_vals['amplitude'], self.prop_vals['wavelength'], self.prop_vals['centre_y'],
                                 self.prop_vals['phase'], self.prop_vals['x_min'], self.prop_vals['x_max'],
                                 self.prop_vals['stroke_width'], self.prop_vals['orientation'],
                                 self.prop_vals['num_points'])])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (self.compute(), None)).save()

POLYGON_NODE_INFO = UnitNodeInfo(
    name="Polygon",
    resizable=True,
    selectable=True,
    in_port_defs=[PortDef("Gradient", PortType.GRADIENT), PortDef("Import Points", PortType.ELEMENT, input_multiple=True)],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList(
        [
            PropType("points", "table", default_value=[(0, 0), (0, 1), (1, 1)],
                     description=""),
            PropType("fill", "colour", default_value=(0, 0, 0, 255),
                     description="")
        ]
    )
)

class PolygonNode(UnitNode):
    UNIT_NODE_INFO = POLYGON_NODE_INFO

    def compute(self):
        gradient = self.input_nodes[0].compute()
        polyline_nodes = self.input_nodes[1:]
        import_elem = polyline_nodes[0].compute()
        if gradient:
            fill = gradient
            fill_opacity = 255
        else:
            fill, fill_opacity = process_rgb(self.prop_vals['fill'])
        # Process input polylines
        polyline_node_ids = []
        if import_elem:
            polyline_node_ids = [pn.node_id for pn in polyline_nodes]
        indices_to_remove = []
        for i, p in enumerate(self.prop_vals['points']):
            if isinstance(p, PointRef):
                if p.node_id in polyline_node_ids:
                    # Polyline found - update its points
                    index = polyline_node_ids.index(p.node_id)
                    p.points = polyline_nodes[index].compute()[0].get_points()
                    polyline_node_ids[index] = None
                else:
                    # Polyline has been removed
                    indices_to_remove.append(i)
        # Remove no longer existing polylines
        for i in reversed(indices_to_remove):
            del self.prop_vals['points'][i]
        # Add new polylines
        for i, pn_id in enumerate(polyline_node_ids):
            if pn_id is not None:
                self.prop_vals['points'].append(PointRef(polyline_nodes[i]))
        # Return element
        return Element([Polygon(self.prop_vals['points'], fill, fill_opacity)])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (self.compute(), None)).save()


RECTANGLE_NODE_INFO = UnitNodeInfo(
    name="Rectangle",
    resizable=True,
    selectable=True,
    in_port_defs=[PortDef("Gradient", PortType.GRADIENT)],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList(
        [
            PropType("fill", "colour", default_value=(0, 0, 0, 255),
                     description="")
        ]
    )
)


class RectangleNode(UnitNode):
    UNIT_NODE_INFO = RECTANGLE_NODE_INFO

    def compute(self):
        gradient = self.input_nodes[0].compute()
        if gradient:
            fill = gradient
            fill_opacity = 255
        else:
            fill, fill_opacity = process_rgb(self.prop_vals['fill'])
        return Element([Polygon([(0, 0), (0, 1), (1, 1), (1, 0)], fill, fill_opacity)])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (self.compute(), None)).save()


ELLIPSE_NODE_INFO = UnitNodeInfo(
    name="Ellipse",
    resizable=True,
    selectable=True,
    in_port_defs=[PortDef("Gradient", PortType.GRADIENT)],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList(
        [
            PropType("rx", "float", default_value=0.5,
                     description=""),
            PropType("ry", "float", default_value=0.5,
                     description=""),
            PropType("fill", "colour", default_value=(0, 0, 0, 255),
                     description="")
        ]
    )
)


class EllipseNode(UnitNode):
    UNIT_NODE_INFO = ELLIPSE_NODE_INFO

    def compute(self):
        gradient = self.input_nodes[0].compute()
        if gradient:
            fill = gradient
            fill_opacity = 255
        else:
            fill, fill_opacity = process_rgb(self.prop_vals['fill'])
        return Element(
            [Ellipse((0.5, 0.5), (self.prop_vals['rx'], self.prop_vals['ry']), fill, fill_opacity, 'none')])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, (self.compute(), None)).save()

def get_node_from_shape(shape: Shape):
    if isinstance(shape, Polygon):
        return PolygonNode(
            uuid.uuid4(),
            [UnitNode(None, None, None)]*2,
            {
                'points': shape.points,
                'fill': rev_process_rgb(shape.fill, shape.fill_opacity)
            }
        )

class ShapeNode(CombinationNode):
    NAME = "Shape"
    SELECTIONS = [PolygonNode, RectangleNode, EllipseNode, SineWaveNode]
