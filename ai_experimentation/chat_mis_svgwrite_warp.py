import svgwrite
import numpy as np

# Parameters
rows = 12
cols = 40
square_height = 20
canvas_width = 1000
canvas_height = rows * square_height

# X-warping function for column edges
def warp_x(t):
    """Maps t in [0,1] to a warped x-position for visual distortion."""
    center = 0.5
    strength = 0.25
    return t + strength * np.sin(2 * np.pi * (t - center))

# Generate warped column edge positions
t_values = np.linspace(0, 1, cols + 1)
x_positions = [warp_x(t) * canvas_width for t in t_values]

# Create SVG drawing
dwg = svgwrite.Drawing("movement_in_squares_warped.svg", size=(canvas_width, canvas_height))

# Draw distorted checkerboard
for row in range(rows):
    y = row * square_height
    for col in range(cols):
        x1 = x_positions[col]
        x2 = x_positions[col + 1]
        w = x2 - x1
        color = 'black' if (row + col) % 2 == 0 else 'white'
        dwg.add(dwg.rect(insert=(x1, y), size=(w, square_height), fill=color))

dwg.save()
