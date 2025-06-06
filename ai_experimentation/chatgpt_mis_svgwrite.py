import svgwrite
import numpy as np

# Parameters
rows = 12
cols = 40
square_size = 20  # base size in pixels
width = 1000
height = rows * square_size

# Distortion function
def distortion(t):
    # t ranges from 0 to 1
    return 1 - 2 * (t - 0.5) ** 2  # parabolic distortion

# Create drawing
dwg = svgwrite.Drawing("movement_in_squares.svg", size=(width, height), profile='tiny')
x_pos = 0

# Precompute widths with distortion
col_widths = []
for col in range(cols):
    t = col / (cols - 1)
    scale = distortion(t)
    w = scale * square_size
    col_widths.append(w)

# Compute x positions
x_positions = [0]
for w in col_widths[:-1]:
    x_positions.append(x_positions[-1] + w)

# Draw the squares
for row in range(rows):
    y = row * square_size
    for col in range(cols):
        x = x_positions[col]
        w = col_widths[col]
        color = 'black' if (row + col) % 2 == 0 else 'white'
        dwg.add(dwg.rect(insert=(x, y), size=(w, square_size), fill=color))

# Save the SVG
dwg.save()
