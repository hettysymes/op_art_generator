import itertools
from typing import cast

from nodes.drawers.draw_graph import create_graph_svg
from nodes.function_datatypes import IdentityFun
from nodes.prop_types import PT_Element, PT_List, PT_Function, PT_Fill, PT_Point, \
    PT_Warp, PT_Number, PT_Grid
from nodes.prop_values import List, Point, Grid, Fill, Colour
from nodes.shape_datatypes import Group, Element, Polygon, Polyline
from nodes.transforms import Scale, Translate
from nodes.warp_datatypes import sample_fun, PosWarp, RelWarp
from vis_types import MatplotlibFig


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


def repeat_shapes(grid: Grid, elements: List[PT_Element], row_iter=True, scale_x=True, scale_y=True):
    ret_group = Group(debug_info="Shape Repeater")
    element_it = itertools.cycle(elements)

    rows = len(grid.h_line_ys) - 1
    cols = len(grid.v_line_xs) - 1

    total_cells = rows * cols
    for idx in range(total_cells):
        if row_iter:
            i, j = divmod(idx, cols)
        else:
            j, i = divmod(idx, rows)

        x1 = grid.v_line_xs[j]
        x2 = grid.v_line_xs[j + 1]
        y1 = grid.h_line_ys[i]
        y2 = grid.h_line_ys[i + 1]
        x_sf = x2 - x1 if scale_x else 1 / cols
        y_sf = y2 - y1 if scale_y else 1 / rows
        cell_group = Group([Scale(x_sf, y_sf), Translate(x1, y1)], debug_info=f"Cell ({i},{j})")
        cell_group.add(next(element_it))
        ret_group.add(cell_group)

    return ret_group


def get_rectangle(fill: Fill, stroke: Fill = Colour(), stroke_width=0):
    return Polygon([Point(0, 0), Point(0, 1), Point(1, 1), Point(1, 0)], fill, stroke, stroke_width)


def draw_grid(grid: Grid) -> Element:
    grid_group = Group(debug_info="Grid")
    for x in grid.v_line_xs:
        # Draw horizontal lines
        grid_group.add(Polyline([(x, 0), (x, 1)], stroke=Colour(0, 0, 0, 255), stroke_width=2))
    for y in grid.h_line_ys:
        # Draw vertical lines
        grid_group.add(Polyline([(0, y), (1, y)], stroke=Colour(0, 0, 0, 255), stroke_width=2))
    return add_background(grid_group, Colour(255, 255, 255, 255))


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
            to_draw = [visualise_by_type(value_item, value_item.type) for value_item in value]
            # If nothing to draw, return None
            if not to_draw:
                return None
            # If not all elements, return None
            for val in to_draw:
                if not isinstance(val, Element):
                    return None
            # Draw elements in a grid
            if value.vertical_layout:
                # Draw vertical grid
                grid = get_grid(height=len(value))
            else:
                # Draw horizontal grid
                grid = get_grid(width=len(value))
            return repeat_shapes(grid, List(PT_Element(), to_draw))
    elif isinstance(value_type, PT_Fill):
        return get_rectangle(value)
    elif isinstance(value_type, PT_Element):
        return value
    elif isinstance(value_type, PT_Function):
        return MatplotlibFig(create_graph_svg(sample_fun(value, 1000)))
    elif isinstance(value_type, PT_Warp):
        return MatplotlibFig(create_graph_svg(value.sample(1000)))
    elif isinstance(value_type, PT_Grid):
        return draw_grid(value)
    else:
        return None
