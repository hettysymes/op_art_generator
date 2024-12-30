import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import math

# Function to parse the SVG file and extract ellipses
def extract_ellipses_from_svg(svg_filename):
    # Parse the SVG file
    tree = ET.parse(svg_filename)
    root = tree.getroot()

    # Define the SVG namespace
    namespace = {"svg": "http://www.w3.org/2000/svg"}

    # Find all ellipse elements
    ellipses = root.findall(".//svg:ellipse", namespaces=namespace)

    ellipse_data = []  # Store ellipse information for plotting
    for ellipse in ellipses:
        cx = float(ellipse.attrib.get("cx", "0"))  # x-coordinate of the center
        cy = float(ellipse.attrib.get("cy", "0"))  # y-coordinate of the center
        rx = float(ellipse.attrib.get("rx", "0"))  # Horizontal radius
        ry = float(ellipse.attrib.get("ry", "0"))  # Vertical radius
        transform = ellipse.attrib.get("transform", None)  # Transformation (if any)

        # Parse transformation (rotation)
        rotation_angle = 0
        if transform and "rotate" in transform:
            rotation_angle = float(transform.split("(")[1].split(")")[0].split()[0])

        ellipse_data.append((cx, cy, rx, ry, rotation_angle))
    
    print(len(ellipse_data))
    return ellipse_data

# Function to plot ellipses using Matplotlib
def plot_ellipses(ellipse_data):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_aspect('equal', adjustable='datalim')

    for cx, cy, rx, ry, rotation_angle in ellipse_data:
        # Create and add an Ellipse patch
        ellipse = Ellipse(
            (cx, cy), width=2*rx, height=2*ry, angle=rotation_angle, edgecolor='black', facecolor='none'
        )
        ax.add_patch(ellipse)
        ax.plot(cx, cy, 'ro')  # Mark the center of the ellipse

    ax.set_xlim(0, 100)  # Adjust limits to match your canvas size
    ax.set_ylim(0, 200)
    plt.gca().invert_yaxis()  # Invert Y-axis to match SVG coordinate system
    plt.grid(True)
    plt.title("Ellipses from SVG")
    plt.xlabel("X-axis")
    plt.ylabel("Y-axis")
    plt.show()

# Main script
svg_filename = "brute_force.svg"

# Extract ellipse information from SVG
ellipse_data = extract_ellipses_from_svg(svg_filename)

# Plot ellipses
plot_ellipses(ellipse_data)
