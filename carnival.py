from Drawing import Drawing
import numpy as np
import random
from utils import SineWave

class Carnival(Drawing):

    def __init__(self, out_name, width, height):
        super().__init__(out_name, width, height)
        self.palette = {"red": "#de4040",
                        "yellow": "#e2bf31",
                        "purple": "#a13d90"
                        }
        self.sine = SineWave(0.031792845*self.width, 0.558472292*self.height)
        self.xshift = 0.048933148 * self.width
        self.yshift = 0.022185698 * self.height
        
    def draw(self):
        self.add_bg(self.palette['yellow'])
        self.draw_polygon(50, 50, self.palette['red'])
        self.draw_polygon(200, 100, self.palette['purple'])

    def draw_polygon(self, trough_x, trough_y, col):
        horizontal_points = self.sine.sample(trough_y, trough_x, 0, self.height)
        wave_points = [(x,y) for (y,x) in horizontal_points]
        horizontal_points = self.sine.sample(trough_y+self.yshift, trough_x+self.xshift, 0, self.height)
        wave_points += reversed([(x,y) for (y,x) in horizontal_points])
        self.dwg_add(self.dwg.polygon(wave_points, fill=col, stroke='none'))


if __name__ == '__main__':
    drawing = Carnival('out/carnival', 1000, 1.36)
    drawing.render()