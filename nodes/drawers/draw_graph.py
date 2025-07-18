import numpy as np
from matplotlib.figure import Figure


def create_graph_svg(ys, xs=None, scatter=False, mirror_img_coords=False, highlight_index=None):
    # Sample the function (1000 points for smooth curve)
    xs = np.linspace(0, 1, len(ys)) if xs is None else xs

    # Create a Figure and plot the data
    fig = Figure()
    ax = fig.add_subplot(111)

    if scatter:
        # Plot all points in blue
        ax.scatter(xs, ys, color='blue', s=2)

        # Highlight the specific point in orange
        if highlight_index is not None and 0 <= highlight_index < len(xs):
            ax.scatter(xs[highlight_index], ys[highlight_index], color='orange', s=10)
    else:
        ax.plot(xs, ys, 'b-', linewidth=2)

    ax.set_xlabel("x")
    ax.set_ylabel("y")

    # Add grid for better readability
    ax.grid(True, alpha=0.3)

    if mirror_img_coords:
        # Set the graph to mirror the image coordinate system
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        # Invert y-axis so that (0,0) is in the top-left corner
        ax.invert_yaxis()

    return fig
