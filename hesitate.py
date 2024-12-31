import svgwrite
import cairosvg
import math

class Drawing:

    def __init__(self, out_name, width, height):
        self.out_name = out_name
        self.width = width
        self.height = height
        self.dwg = svgwrite.Drawing(f'{out_name}.svg', size=(width, height))
        
    def draw(self):
        # Add background
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height), fill="white"))
        # Define merge centre x position
        merge_x = self.width * 3/8
        # Add rectangle stripes
        start = True
        switch = False
        ellipse_rh = 10
        x_pos = 0
        while x_pos < self.width:
            # Use sigmoid fun to find rectangle width
            # 1.5 is arbitrary scaling factor for "sharper" curve
            d = 1.5*abs(merge_x - x_pos)
            sigmoid = lambda z: 1/(1 + math.exp(-z))
            # Consider sigmoid range [a, b]
            a = -2.3
            b = 4
            # When x is high, sigmoid is close to 1 so rect_w is approx rect_h
            ellipse_rw = ellipse_rh * sigmoid(a + (d/merge_x) * (b-a))
            self.add_verticle_stripe(ellipse_rw, ellipse_rh, x_pos, start)
            x_pos += 2*ellipse_rw
            start = not start

    # x_pos is left border of line
    def add_verticle_stripe(self, ellipse_rx, ellipse_ry, x_pos, start=True):
        y_pos = 0
        if not start:
            # White area starts
            y_pos += 2*ellipse_ry
        while y_pos < self.height:
            self.dwg.add(self.dwg.ellipse(
                            center=(x_pos, y_pos),
                            r=(ellipse_rx, ellipse_ry),
                            fill='black',
                        ))
            y_pos += 4*ellipse_ry
                    
    def save(self):
        self.dwg.save()
        cairosvg.svg2png(url=f"{self.out_name}.svg", write_to=f"{self.out_name}.png")

if __name__ == '__main__':
    drawing = Drawing('out/hesitate', 400, 400)
    drawing.draw()
    drawing.save()
    print("SVG and PNG files saved.")