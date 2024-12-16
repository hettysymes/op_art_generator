import svgwrite
import cairosvg
import math
import numpy as np

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

    def bezier_pt_calc(self, t, P0, P1, P2):
        x = (1-t)**2 * P0[0] + 2*(1-t)*t * P1[0] + t**2 * P2[0]
        y = (1-t)**2 * P0[1] + 2*(1-t)*t * P1[1] + t**2 * P2[1]
        return (x, y)
    
    def circle_pt(self, theta, t, dip_pt, circle_rad, inter_rad, inter_theta):
        pt = self.polar_coords(inter_rad, inter_theta)
        end = self.polar_coords(circle_rad, theta)
        return self.bezier_pt_calc(t, dip_pt, pt, end)
    
    def bilinear_interp(self, a_vec, b_vec, c_vec, alpha, beta):
        return alpha*a_vec + beta*b_vec + alpha*beta*(c_vec - b_vec)

    def draw(self):
        # Add background
        self.dwg.add(self.dwg.rect(insert=(-self.width//2, -self.height//2), size=(self.width, self.height), fill="white"))
        dip_pt = (-50,0)
        circle_rad = 150
        inter_rad = 50
        # self.dwg.add(self.dwg.circle(center=(0,0), r=circle_rad, stroke='black', fill='none', opacity=self.opacity))
        # self.dwg.add(self.dwg.circle(center=(0,0), r=inter_rad, stroke='blue', fill='none', opacity=self.opacity))

        max_thetas = 50
        thetas = [(360/max_thetas) * i for i in range(max_thetas)]
        ts = np.linspace(0, 1, 20)
        arc_points = [[] for _ in range(max_thetas)]
        for i, theta in enumerate(thetas):
            inter_theta = theta
            for t in ts:
                arc_points[i].append(self.circle_pt(theta, t, dip_pt, circle_rad, inter_rad, inter_theta))
        for angle_index, points in enumerate(arc_points):
            for t_index in range(len(points)):
                if t_index == 0 or t_index >= len(ts)-1:
                    continue
                prev_arc_points = arc_points[(angle_index-1) % len(arc_points)]
                next_arc_points = arc_points[(angle_index+1) % len(arc_points)]
                P1 = np.array(prev_arc_points[t_index-1])
                P2 = np.array(prev_arc_points[t_index+1])
                P3 = np.array(next_arc_points[t_index+1])
                P4 = np.array(next_arc_points[t_index-1])
                # interpolate
                a_vec = P4-P1
                b_vec = P2-P1
                c_vec = P3-P4
                centre = P1 + self.bilinear_interp(a_vec, b_vec, c_vec, 0.5, 0.5)
                rv = np.linalg.norm(b_vec + 0.5*(c_vec - b_vec))/2
                b_vec = P3-P2
                c_vec = P4-P1
                rh = np.linalg.norm(b_vec + 0.5*(c_vec - b_vec))/2
                scale = 0.3
                self.dwg.add(self.dwg.ellipse(center=centre, r=(rh*scale, rv*scale)))

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