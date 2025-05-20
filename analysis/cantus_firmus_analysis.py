import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Load Data
file_path = "op_art_analysis.xlsx"
xls = pd.ExcelFile(file_path)
df = pd.read_excel(xls, sheet_name="Cantus Firmus")

# Plot line graph
plt.figure(figsize=(10, 5))
plt.plot(df['x'], df['Width'], linestyle='-', color='black')  # Line in black

if 'Colour' not in df.columns or 'Width' not in df.columns:
    raise ValueError("Ensure the Excel file has 'colour' and 'Width' columns.")

colour_hex = {'green': '#c4cb3aff', 'pink': '#d38aaaff', 'blue': '#7dbbd3ff',
              'white': '#f5f9f4ff', 'black': '#3c3c3cff', 'grey0': '#acabaeff',
              'grey1': '#97989aff', 'grey2': '#818085ff', 'grey3': '#6e7374ff',
              'grey4': '#5d6160ff', 'grey5': '#4c4950ff', 'grey6': '#434348ff'}
widths = {'green':[], 'pink':[], 'blue':[], 'white':[], 'black':[]}
grey_xs = []

# Apply colors to data points
for (x, width, colour) in zip(df['x'], df['Width'], df['Colour']):
    hex_val = colour_hex[colour]
    if colour in widths: widths[colour].append(width)
    if colour[:4] == 'grey': grey_xs.append(x)
    plt.scatter(x, width, color=hex_val, edgecolors='black', s=100)  # s controls size

widths['green'] = widths['green'][1:]
for colour in ['green', 'pink', 'blue', 'white', 'black']:
    print(f"Mean {colour} width: {np.round(np.mean(widths[colour]), 5)}")


# Labels and grid
plt.xlabel("Index")
plt.ylabel("Width")
plt.grid(True)

# Show the plot
plt.savefig("width_plot.svg", format="svg")

plt.clf()
# Extract signal (Width values)
widths = df['Width']
y = widths - np.mean(widths)
N = len(y)  # Number of data points
T = 1  # Assume unit time steps (adjust if you have actual time intervals)

# Apply Fourier Transform
fft_values = np.fft.fft(y)
frequencies = np.fft.fftfreq(N, T)  # Get frequency bins

# Plot Fourier Transform (Magnitude Spectrum)
plt.plot(frequencies[:N//2], np.abs(fft_values[:N//2]), color='red')  # Only positive frequencies
plt.xlabel("Frequency")
plt.ylabel("Magnitude")
plt.grid(True)

plt.tight_layout()
plt.savefig("fourier_plot.svg", format="svg")

grey_shades = ['#a9acb4', '#939997', '#7f7f8c', '#73737a', '#5c6164', '#4f4c4f', '#444444', '#3e3c3d', '#4c4f54', '#717876', '#858686', '#bababc']

def hex_to_rgb(hex_color):
    """Convert hex color (#RRGGBB) to an (R, G, B) tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def simple_average(hex_color):
    """Calculate intensity using simple averaging of RGB values."""
    r, g, b = hex_to_rgb(hex_color)
    return (r + g + b) / 3

grey_intensities = [simple_average(colour) for colour in grey_shades]

# Plot
plt.clf()
plt.figure(figsize=(8, 5))
scatter = plt.scatter(grey_xs, grey_intensities)

# # Annotate each point with more control
# for i in range(len(grey_xs)):
#     plt.annotate(f"({grey_xs[i]}, {grey_intensities[i]})", (grey_xs[i], grey_intensities[i]), textcoords="offset points", xytext=(5,5), ha='left', fontsize=10, color="red")

# Labels and Title
plt.xlabel("Grey X Positions")
plt.ylabel("Intensity (0-255)")
# plt.title("Color Intensity (Brightness) Visualization")
plt.ylim(0, 255)  # Brightness scale (0 to 255)
plt.xticks(rotation=45)
plt.grid(True)
plt.savefig("colour_brightness.svg", format="svg")