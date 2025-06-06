import matplotlib.pyplot as plt
import numpy as np

# Parameters
rows = 12
cols = 40
width = 1
height = 1

# Distortion function for x-scaling
def distortion(col, total_cols):
    # Normalized col index from 0 to 1
    t = col / total_cols
    # Scale gets tighter towards the center
    if t < 0.5:
        return 1 - 2 * (0.5 - t)**2
    else:
        return 1 - 2 * (t - 0.5)**2

# Create the figure and axis
fig, ax = plt.subplots(figsize=(12, 6))
ax.set_aspect('equal')
ax.axis('off')

# Draw squares with distortion
for row in range(rows):
    for col in range(cols):
        scale = distortion(col, cols - 1)
        x = sum(distortion(c, cols - 1) * width for c in range(col))
        y = row * height
        color = 'black' if (row + col) % 2 == 0 else 'white'
        rect = plt.Rectangle((x, y), width * scale, height, color=color)
        ax.add_patch(rect)

# Adjust the axis limits
ax.set_xlim(0, sum(distortion(c, cols - 1) * width for c in range(cols)))
ax.set_ylim(0, rows * height)

plt.tight_layout()
plt.show()
