import xml.etree.ElementTree as ET

def extract_circles_from_svg(svg_file):
    # Parse the SVG file
    tree = ET.parse(svg_file)
    root = tree.getroot()
    
    # SVG namespace handling
    namespace = {'svg': 'http://www.w3.org/2000/svg'}

    # Find all circle elements
    circles = root.findall('.//svg:circle', namespace)
    
    # Extract circle data
    circle_info = []
    for circle in circles:
        cx = circle.attrib.get('cx', '0')  # Default to '0' if not present
        cy = circle.attrib.get('cy', '0')
        r = circle.attrib.get('r', '0')
        circle_info.append({'cx': float(cx), 'cy': float(cy), 'r': float(r)})
    
    return circle_info

"""
def draw_pt(self, centre, col='green', rad=1):
        self.dwg.add(self.dwg.circle(center=centre, r=rad, fill=col))
"""

# Usage
svg_file_path = "blaze_analysis.svg"  # Replace with the path to your SVG file
circle_data = extract_circles_from_svg(svg_file_path)
print(circle_data)
print(len(circle_data))
