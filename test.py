import svgwrite
import cairosvg
import math

class Drawing:

    def __init__(self, out_name, width, height):
        self.out_name = out_name
        self.width = width
        self.height = height
        self.dwg = svgwrite.Drawing(f'{out_name}.svg', size=(width, height))
        self.set_viewbox()

    # View box is such that (0,0) is the centre of the image
    def set_viewbox(self, top_bot_crop=10):
        self.dwg.viewbox(minx=-self.width//2, 
                         miny=-self.height//2, 
                         width=self.width, 
                         height=self.height - 2*top_bot_crop)
        
    def draw(self):
        # Add background
        self.dwg.add(self.dwg.rect(insert=(-self.width//2, -self.height//2), size=(self.width, self.height), fill="white"))
        n_polygons = 16
        separation = 30
        phase = 0
        shift = 0.5
        grad_end_sine_pts = []
        for i in range(-n_polygons//2, n_polygons//2):
            points = self.add_vertical_sine_wave_polygon(i*separation, fill='black', phase_shift1=phase, phase_shift2=phase+shift)
            phase += 2*shift
            if i == 0:
                grad_end_sine_pts = points[:100]
        grad_id = self.create_linear_gradient()
        # Add first gradient
        path = self.create_line_path(grad_end_sine_pts + [(-self.width//2, self.height//2), (-self.width//2, -self.height//2)], fill=f'url(#{grad_id})', colour='none')
        path.push('Z')
        self.dwg.add(path)
        # Add second gradient
        path = self.create_line_path(grad_end_sine_pts + [(self.width//2, self.height//2), (self.width//2, -self.height//2)], fill=f'url(#{grad_id})', colour='none')
        path.push('Z')
        self.dwg.add(path)


    def create_linear_gradient(self, colour='white'):
        grad_id = 'white_lin_grad'
        gradient = self.dwg.linearGradient(id=grad_id, start=(0, 0), end=(1, 0))  # From left to right
        gradient.add_stop_color(offset=0, opacity=0)  # Start with transparent
        gradient.add_stop_color(offset=1, color=colour)  # End with white
        self.dwg.defs.add(gradient)
        return grad_id

    # Plots vertical sine wave centered at x_pos starting at y_start, ranging for y_len
    @staticmethod
    def vertical_sine_wave(x_pos, y_start, y_len, phase_shift=0, amplitude=50, frequency=3, num_points=100):
        # Generate sine wave points
        points = []
        for i in range(num_points):
            y = y_start + i * (y_len / num_points)
            x = x_pos + amplitude * math.sin(2 * math.pi * frequency * (i / num_points) + phase_shift)
            points.append((x, y))
        return points
    
    def add_vertical_sine_wave_polygon(self, x_pos, width=15, fill='blue', phase_shift1=0, phase_shift2=0.5, amplitude=10, frequency=3, num_points=100):
        sine1_pts = Drawing.vertical_sine_wave(x_pos-width//2, -self.height//2, self.height, phase_shift=phase_shift1, amplitude=amplitude, frequency=frequency, num_points=num_points)
        sine2_pts = Drawing.vertical_sine_wave(x_pos+width//2, -self.height//2, self.height, phase_shift=phase_shift2, amplitude=amplitude, frequency=frequency, num_points=num_points)
        sine2_pts.reverse()
        points = sine1_pts + sine2_pts
        path = self.create_line_path(points, fill=fill, colour=fill)
        path.push('Z')
        self.dwg.add(path)
        return points
    
    # Plots vertical sine wave centered at x_pos starting at y_start, ranging for y_len
    def create_line_path(self, points, colour='blue', fill='none', stroke_width=1):
        path = self.dwg.path(stroke=colour, fill=fill, stroke_width=stroke_width)
        path.push('M', points[0][0], points[0][1])  # Move to start point
        for i in range(1, len(points)):
            path.push('L', points[i][0], points[i][1])
        return path

    def save(self):
        self.dwg.save()
        cairosvg.svg2png(url=f"{self.out_name}.svg", write_to=f"{self.out_name}.png")

if __name__ == '__main__':
    drawing = Drawing('out/example', 400, 400)
    drawing.draw()
    drawing.save()
    print("SVG file saved.")