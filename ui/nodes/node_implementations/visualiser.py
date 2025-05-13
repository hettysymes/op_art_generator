import itertools

from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.function_datatypes import IdentityFun
from ui.nodes.gradient_datatype import Gradient
from ui.nodes.port_defs import PT_Colour, PT_Element, PT_List, PT_Function, PT_Fill
from ui.nodes.shape_datatypes import Group, Element, Polygon
from ui.nodes.transforms import Scale, Translate
from ui.nodes.utils import process_rgb
from ui.nodes.warp_datatypes import sample_fun, PosWarp, RelWarp
from ui.vis_types import MatplotlibFig

def get_grid(width=1, height=1, x_warp=None, y_warp=None):
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
    return v_line_xs, h_line_ys

def repeat_shapes(grid, elements):
    v_line_xs, h_line_ys = grid
    ret_group = Group(debug_info="Shape Repeater")
    if isinstance(elements, Element):
        # Ensure elements is a list
        elements = [elements]
    element_it = itertools.cycle(elements)
    for i in range(0, len(h_line_ys) - 1):
        # Add row
        for j in range(0, len(v_line_xs) - 1):
            x1 = v_line_xs[j]
            x2 = v_line_xs[j + 1]
            y1 = h_line_ys[i]
            y2 = h_line_ys[i + 1]
            cell_group = Group([Scale(x2 - x1, y2 - y1), Translate(x1, y1)], debug_info=f"Cell ({i},{j})")
            cell_group.add(next(element_it))
            ret_group.add(cell_group)
    return ret_group

def get_polygon(fill, points, stroke, stroke_width):
    if isinstance(fill, Gradient):
        fill_opacity = 255
    else:
        fill, fill_opacity = process_rgb(fill)
    return Polygon(points, fill, fill_opacity, stroke, stroke_width)

def get_rectangle(fill, stroke='none', stroke_width=0):
    return get_polygon(fill, [(0, 0), (0, 1), (1, 1), (1, 0)], stroke, stroke_width)

def visualise_in_1d_grid(elements, is_vertical=True):
    if is_vertical:
        grid = get_grid(height=len(elements))
    else:
        grid = get_grid(width=len(elements))
    return repeat_shapes(grid, elements)

def visualise_by_type(value, value_type):
    if not value:
        return None
    elif isinstance(value_type, PT_List):
        # Draw vertical grid
        grid = get_grid(height=len(value))
        elements = [visualise_by_type(value_item, value_type.item_type) for value_item in value]
        if (not elements) or not all(isinstance(e, Element) for e in elements):
            return None
        return repeat_shapes(grid, elements)
    elif isinstance(value_type, PT_Fill):
        return get_rectangle(value)
    elif isinstance(value_type, PT_Element):
        return value
    elif isinstance(value_type, PT_Function):
        return MatplotlibFig(create_graph_svg(sample_fun(value, 1000)))
    else:
        return None