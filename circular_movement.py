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
        self.opacity = 0.1

    # View box is such that (0,0) is the centre of the image
    def set_viewbox(self):
        self.dwg.viewbox(minx=-self.width//2, 
                         miny=-self.height//2, 
                         width=self.width, 
                         height=self.height)

    def draw(self):
        # Add background
        self.dwg.add(self.dwg.rect(insert=(-self.width//2, -self.height//2), size=(self.width, self.height), fill="white"))
        dip_pt = (-50,0)
        circle_rad = 150
        inter_rad = 100
        self.dwg.add(self.dwg.circle(center=(0,0), r=circle_rad, stroke='black', fill='none', opacity=self.opacity))
        self.dwg.add(self.dwg.circle(center=(0,0), r=inter_rad, stroke='blue', fill='none', opacity=self.opacity))

        max_pts = 50
        for i in range(max_pts):
            theta = (360/max_pts) * i
            inter_theta = theta
            pt = self.polar_coords(inter_rad, inter_theta)
            end = self.polar_coords(circle_rad, theta)
            self.draw_bezier(dip_pt, pt, end)

    def draw_bezier(self, start, pt, end):
        opacity = 0.3
        self.dwg.add(self.dwg.circle(center=start, r=2))
        self.dwg.add(self.dwg.circle(center=pt, r=2, fill='red', opacity=self.opacity))
        self.dwg.add(self.dwg.circle(center=end, r=2))
        self.bezier(start, pt, end)
        self.dwg.add(self.dwg.line(start, pt, stroke='red', opacity=self.opacity))
        self.dwg.add(self.dwg.line(pt, end, stroke='red', opacity=self.opacity))

    def polar_coords(self, r, theta, c=(0,0)):
        theta_rad = math.radians(theta)
        x = c[0] + r * math.cos(theta_rad)
        y = c[1] - r * math.sin(theta_rad)
        return (x,y)

    def bezier(self, start, pt, end):
        path_data = f"M {start[0]},{start[1]} Q {pt[0]},{pt[1]} {end[0]},{end[1]}"
        self.dwg.add(self.dwg.path(d=path_data, stroke='black', fill='none'))
                    
    def save(self):
        self.dwg.save()
        cairosvg.svg2png(url=f"{self.out_name}.svg", write_to=f"{self.out_name}.png")

if __name__ == '__main__':
    drawing = Drawing('out/circular_movement', 400, 400)
    drawing.draw()
    drawing.save()
    print("SVG and PNG files saved.")