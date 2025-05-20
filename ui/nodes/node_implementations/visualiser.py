import itertools
from typing import cast

from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.function_datatypes import IdentityFun
from ui.nodes.gradient_datatype import Gradient
from ui.nodes.prop_defs import PT_Element, PT_List, PT_Function, PT_Fill, PropValue, Colour, Grid, List, PT_Point, \
    Point, PT_Warp, PT_Number
from ui.nodes.shape_datatypes import Group, Element, Polygon
from ui.nodes.transforms import Scale, Translate
from ui.nodes.utils import process_rgb
from ui.nodes.warp_datatypes import sample_fun, PosWarp, RelWarp
from ui.vis_types import MatplotlibFig


def add_background(element: Element, colour: Colour):
    group = Group(debug_info="Background")
    group.add(get_rectangle(colour))
    if element:
        group.add(element)
    return group


def get_grid(width=1, height=1, x_warp=None, y_warp=None) -> Grid:
    if x_warp is None:
        x_warp = PosWarp(IdentityFun())
    else:
        assert isinstance(x_warp, PosWarp) or isinstance(x_warp, RelWarp)

    if y_warp is None:
        y_warp = PosWarp(IdentityFun())
    else:
        assert isinstance(y_warp, PosWarp) or isinstance(y_warp, RelWarp)

    v_line_xs = x_warp.sample(width + 1)
    h_line_ys = y_warp.sample(height + 1)
    return Grid(v_line_xs, h_line_ys)


def repeat_shapes(grid: Grid, elements: List[PT_Element]):
    ret_group = Group(debug_info="Shape Repeater")
    element_it = itertools.cycle(elements)
    for i in range(0, len(grid.h_line_ys) - 1):
        # Add row
        for j in range(0, len(grid.v_line_xs) - 1):
            x1 = grid.v_line_xs[j]
            x2 = grid.v_line_xs[j + 1]
            y1 = grid.h_line_ys[i]
            y2 = grid.h_line_ys[i + 1]
            cell_group = Group([Scale(x2 - x1, y2 - y1), Translate(x1, y1)], debug_info=f"Cell ({i},{j})")
            cell_group.add(next(element_it))
            ret_group.add(cell_group)
    return ret_group


def get_polygon(fill: PropValue, points: List[PT_Point], stroke, stroke_width):
    if isinstance(fill, Gradient):
        fill_opacity = 255
    elif isinstance(fill, Colour):
        fill, fill_opacity = process_rgb(fill)
    else:
        assert False
    return Polygon(points, fill, fill_opacity, stroke, stroke_width)


def get_rectangle(fill: Gradient | Colour, stroke='none', stroke_width=0):
    return get_polygon(fill, List(PT_Point(), [Point(0, 0), Point(0, 1), Point(1, 1), Point(1, 0)]), stroke,
                       stroke_width)


def visualise_by_type(value, value_type):
    if value is None:
        return None
    elif isinstance(value_type, PT_List):
        if isinstance(value_type.base_item_type, PT_Number) and value_type.depth == 1:
            return MatplotlibFig(create_graph_svg(value.items, scatter=True))
        elif isinstance(value_type.base_item_type, PT_Point) and value_type.depth == 1:
            xs, ys = zip(*value.items)
            return MatplotlibFig(create_graph_svg(ys, xs=xs, scatter=True, mirror_img_coords=True))
        else:
            value = cast(List, value)
            if value.vertical_layout:
                # Draw vertical grid
                grid = get_grid(height=len(value))
            else:
                # Draw horizontal grid
                grid = get_grid(width=len(value))
            elements = List(PT_Element(),
                            [visualise_by_type(value_item, value.item_type) for value_item in value])
            if not elements:
                return None
            return repeat_shapes(grid, elements)
    elif isinstance(value_type, PT_Fill):
        return get_rectangle(value)
    elif isinstance(value_type, PT_Element):
        return value
    elif isinstance(value_type, PT_Function):
        return MatplotlibFig(create_graph_svg(sample_fun(value, 1000)))
    elif isinstance(value_type, PT_Warp):
        return MatplotlibFig(create_graph_svg(value.sample(1000)))
    else:
        return None
