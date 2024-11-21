import svgwrite
import cairosvg

out_name = 'out/example'

# Define SVG size explicitly
dwg = svgwrite.Drawing(f'{out_name}.svg', size=("200px", "200px"))

# Add a circle
dwg.add(dwg.circle(center=(100, 100), r=50, stroke='black', fill='red'))

# Add text
dwg.add(dwg.text('Hello SVG', insert=(50, 150), fill='blue', font_size='20px'))

# Save the file
dwg.save()

print("SVG file created successfully.")

# Convert SVG file to PNG
cairosvg.svg2png(url=f"{out_name}.svg", write_to=f"{out_name}.png")

print("SVG file converted to PNG successfully.")