from svgpathtools import svg2paths

def complex_to_coord(complex):
    return (complex.real, complex.imag)

def get_cubic_beziers(svg_file):
    beziers = []

    paths, _ = svg2paths(svg_file)
    for path in paths:
        for segment in path:
            if segment.__class__.__name__ == 'CubicBezier':
                info = [segment.start, segment.control1, segment.control2, segment.end]
                beziers.append([complex_to_coord(p) for p in info])
                
    
    return beziers