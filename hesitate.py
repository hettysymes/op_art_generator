import svgwrite
import subprocess
from utils import CubicBezierCurve, Ellipse, ColourIterator
import math

class Drawing:

    def __init__(self, out_name, width, height):
        self.out_name = out_name
        self.width = width
        self.height = height
        self.dwg = svgwrite.Drawing(f'{out_name}.svg', size=(width, height))

        # Define a clipping path that matches the viewBox size
        clip = self.dwg.defs.add(self.dwg.clipPath(id="clip-area"))
        clip.add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height)))

        # Parameters
        self.rx = 0.02*self.width
        scale = 0.052
        min_ry = 0.001
        self.merge_idx = 0.365
        self.ry_fun = lambda idx: min(scale*abs(idx-self.merge_idx)+min_ry, 0.02)

        self.gradient1 = CubicBezierCurve([(0.36754503,197.35298), (90.31066,101.13119), (147.20573,59.949696), (208.38394,59.714716)])
        self.ellipses = [] # TODO: what if is not rectangle?
        

    def dwg_add(self, element):
        element['clip-path'] = "url(#clip-area)"
        self.dwg.add(element)

    def draw(self):
        # Add background
        self.dwg_add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height), fill="#eceeeb"))

        start = True
        prev_boundary = 0
        i = 0
        while prev_boundary < self.width:
            ry = self.ry_fun(i/36)*self.height
            self.add_row(prev_boundary + ry, ry, start)
            start = not start
            i += 1
            prev_boundary +=  2*ry
        
        for row in self.ellipses:
            for ellipse in row:
                self.dwg_add(self.dwg.ellipse(
                                    center=(ellipse.cx, ellipse.cy),
                                    r=(ellipse.rx, ellipse.ry),
                                    fill='black',
                                ))

        # curve_assignment = [[None for _ in range(len(self.ellipses[0]))] for _ in range(len(self.ellipses))]
        # assignment = 0
        # for i in range(len(self.ellipses)):
        #     for j in range(len(self.ellipses[0])):
        #         upper_coord = (i-1, j+1 if i%2==1 else j)
        #         if upper_coord[0] < 0 or upper_coord[1] >= len(self.ellipses[0]):
        #             curve_assignment[i][j] = assignment
        #             assignment += 1
        #         else:
        #             curve_assignment[i][j] = curve_assignment[upper_coord[0]][upper_coord[1]]
        
        # Draw
        # left_assignment = 13
        # centre_assignment = 19
        # right_assignment = 25
        # left_points = []
        # centre_points = []
        # right_points = []
        # # col_it = ColourIterator(["black", "purple"])
        # for i in range(len(self.ellipses)):
        #     for j in range(len(self.ellipses[0])):
        #         ellipse = self.ellipses[i][j]
        #         assignment = curve_assignment[i][j]
        #         col = "black"
        #         if assignment == left_assignment:
        #             left_points.append((ellipse.cx, ellipse.cy))
        #         elif assignment == centre_assignment:
        #             centre_points.append((ellipse.cx, ellipse.cy))
        #         elif assignment == right_assignment:
        #             right_points.append((ellipse.cx, ellipse.cy))
        #         self.dwg.add(self.dwg.ellipse(
        #                     center=(ellipse.cx, ellipse.cy),
        #                     r=(ellipse.rx, ellipse.ry),
        #                     fill=col,
        #                 ))

        #self.add_gradients(left_points, centre_points, right_points)

    def add_row(self, y_pos, ry, start=True):
        row = []
        x_pos = self.rx if start else self.rx*3
        while x_pos < self.width:
            # Add ellipse
            row.append(Ellipse(x_pos, y_pos, self.rx, ry))
            x_pos += self.rx*4
        self.ellipses.append(row)

    def add_gradients(self, left_points, centre_points, right_points):
        # Loop through each pair of points in the center line
        right_points.reverse()
        polygon_points = left_points + [(0,self.height)] + right_points
        self.dwg_add(self.dwg.polygon(points=polygon_points, fill='none', stroke='green'))
        self.dwg_add(self.dwg.polyline(points=centre_points, stroke='blue', fill="none"))

    def save(self):
        

        self.dwg.save()
        input_svg = f"{self.out_name}.svg"
        output_png = f"{self.out_name}.png"
        try:
            # Run the Inkscape command
            subprocess.run([
                "/Applications/Inkscape.app/Contents/MacOS/inkscape",
                input_svg,
                "--export-filename", output_png
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    drawing = Drawing('out/hesitate', 207, 197)
    drawing.draw()
    drawing.save()
    print("SVG and PNG files saved.")