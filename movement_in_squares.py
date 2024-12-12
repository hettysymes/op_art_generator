import svgwrite
import cairosvg
import math

class Drawing:

    def __init__(self, out_name, width, height):
        self.out_name = out_name
        self.width = width
        self.height = height
        top_bot_crop = 5
        self.dwg = svgwrite.Drawing(f'{out_name}.svg', size=(width, height-2*top_bot_crop))
        self.set_viewbox(top_bot_crop)

    # View box is such that (0,0) is the centre of the image
    def set_viewbox(self, top_bot_crop):
        self.dwg.viewbox(minx=-self.width//2, 
                         miny=-self.height//2 + top_bot_crop, 
                         width=self.width, 
                         height=self.height - 2*top_bot_crop)
        
    def draw(self):
        # Add background
        self.dwg.add(self.dwg.rect(insert=(-self.width//2, -self.height//2), size=(self.width, self.height), fill="white"))
        # Add rectangle stripes
        start = True
        rect_w = 20
        for x_pos in range(-self.width//2, self.width//2, rect_w):
            self.add_verticle_stripe(rect_w, 20, x_pos, start)
            start = not start

    # x_pos is left border of line
    def add_verticle_stripe(self, rect_w, rect_h, x_pos, start=True):
        y_pos = -self.height//2
        if not start:
            # White rectangle starts
            y_pos += rect_h
        while y_pos < self.height//2:
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
    drawing = Drawing('out/movement_in_squares', 400, 400)
    drawing.draw()
    drawing.save()
    print("SVG and PNG files saved.")