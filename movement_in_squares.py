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
        merge_x = self.width * 5/8
        # Add rectangle stripes
        start = True
        w_scaling = 30
        rect_h = 30
        x_pos = 0
        while x_pos < self.width:
            # Use sigmoid fun to find rectangle width
            x = abs(merge_x - x_pos)
            sigmoid = lambda z: 1/(1 + math.exp(-z))
            # Consider sigmoid range [a, b]
            a = -2
            b = 4
            rect_w = w_scaling * sigmoid(a + (x/merge_x) * (b-a))
            self.add_verticle_stripe(rect_w, rect_h, x_pos, start)
            x_pos += rect_w
            start = not start

    # x_pos is left border of line
    def add_verticle_stripe(self, rect_w, rect_h, x_pos, start=True):
        y_pos = 0
        if not start:
            # White rectangle starts
            y_pos += rect_h
        while y_pos < self.height:
            self.dwg.add(self.dwg.rect(
                            insert=(x_pos, y_pos),
                            size=(rect_w, rect_h),
                            fill='black',
                        ))
            y_pos += 2*rect_h
                    
    def save(self):
        self.dwg.save()
        cairosvg.svg2png(url=f"{self.out_name}.svg", write_to=f"{self.out_name}.png")

if __name__ == '__main__':
    drawing = Drawing('out/movement_in_squares', 360, 360)
    drawing.draw()
    drawing.save()
    print("SVG and PNG files saved.")