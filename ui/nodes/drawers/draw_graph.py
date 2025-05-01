import numpy as np
from matplotlib.figure import Figure


def create_graph_svg(height, wh_ratio, y, filepath, scatter=False):
    # Sample the function (1000 points for smooth curve)
    x = np.linspace(0, 1, len(y))

    # Create a Figure and plot the data
    width = wh_ratio * height
    dpi = 100
    fig = Figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    ax = fig.add_subplot(111)

    if scatter:
        ax.scatter(x, y, color='blue', s=2)  # s controls the marker size
    else:
        ax.plot(x, y, 'b-', linewidth=2)

    ax.set_xlabel("x")
    ax.set_ylabel("y")

    # Add grid for better readability
    ax.grid(True, alpha=0.3)

    fig.savefig(filepath, format='svg', bbox_inches='tight')
    return filepath, None
