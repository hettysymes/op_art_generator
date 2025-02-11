from Drawing import Drawing
import numpy as np
import random

class Conversation(Drawing):

    def __init__(self, out_name, width, height):
        super().__init__(out_name, width, height)
        self.rh = 0.046402567 * self.height
        self.rw = 0.045651261 * self.width
        self.rdh = 0.064379756 * self.height
        self.palette = {"gold": "#d8b240",
                        "dark blue": "#475b90",
                        "yellow": "#e7e087",
                        "light blue": "#b3d0f3",
                        "white": "#eff5f4",
                        "medium green": "#b3cf75",
                        "medium blue": "#5497e5",
                        "dark green": "#64af6b",
                        "red": "#e67459",
                        "black": "#4a4b50",
                        "pink": "#e7d2db",
                        "dark teal": "#42b3ac",
                        "light teal": "#acefd1"
                        }
        
    def draw(self):
        self.add_bg()
        x = self.rw
        y = 0
        while x < self.width+self.rw:
            self.draw_column(x, y)
            x += self.rw
            y -= self.rdh
    
    def draw_6_block(self, col1, col2, x, y):
        for i in range(6):
            col = col1 if i%2 == 0 else col2
            self.draw_rhombus(x, y, col)
            y += self.rh
        return y

    # x,y is coordinate of top-right corner of rhombus
    def draw_rhombus(self, x, y, colour):
        self.dwg_add(self.dwg.polygon(points=[(x,y), (x,y+self.rh), (x-self.rw,y+self.rdh+self.rh), (x-self.rw,y+self.rdh)], 
                                      fill=colour))
        
    def draw_column(self, x, y):
        while y < self.height:
            col1, col2 = [hex_code for _, hex_code in random.sample(list(self.palette.items()), 2)]
            y = self.draw_6_block(col1, col2, x, y)


if __name__ == '__main__':
    drawing = Conversation('out/conversation', 1000, 1.38)
    drawing.render()