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
        merge_x = self.width * 3/4
        # Add rectangle stripes
        start = True
        original_rect_w = 30
        rect_h = 30
        scale = 1
        x_pos = 0
        while x_pos < self.width:
            rect_w = original_rect_w * scale
            if rect_w < 1:
                break
            self.add_verticle_stripe(rect_w, rect_h, x_pos, start)
            x_pos += rect_w
            start = not start
            # Closer to merge x, bigger shrink scaling
            scale = abs(x_pos - merge_x)/300

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