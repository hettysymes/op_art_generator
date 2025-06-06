import svgwrite
import numpy as np

# Canvas settings
canvas_width = 800
canvas_height = 800
num_waves = 10
num_points = 100  # Vertical resolution
wave_amplitude = 40
wave_frequency = 2  # number of full sine cycles per column

# Color palette (black, white, and multiple grays)
colors = ['#1c1c1c', '#4d4d4d', '#7f7f7f', '#b2b2b2', '#e6e6e6']

# Initialize drawing
dwg = svgwrite.Drawing("bridget_riley_arrest2.svg", size=(canvas_width, canvas_height))

# Generate vertical wave columns
column_width = canvas_width / num_waves
for i in range(num_waves):
    x_offset = i * column_width
    path = svgwrite.path.Path(fill=colors[i % len(colors)], stroke="none")

    # Start at the top
    y_vals = np.linspace(0, canvas_height, num_points)
    x_vals_left = [
        x_offset + wave_amplitude * np.sin(2 * np.pi * wave_frequency * y / canvas_height)
        for y in y_vals
    ]
    x_vals_right = [
        x + column_width / 2 for x in x_vals_left
    ]

    # Construct the left curve (down)
    path.push(f"M{x_vals_left[0]},{y_vals[0]}")
    for x, y in zip(x_vals_left[1:], y_vals[1:]):
        path.push(f"L{x},{y}")

    # Construct the right curve (up)
    for x, y in zip(reversed(x_vals_right), reversed(y_vals)):
        path.push(f"L{x},{y}")

    path.push("Z")  # Close the path
    dwg.add(path)

# Save SVG file
dwg.save()
