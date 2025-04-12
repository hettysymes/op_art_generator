from Drawing import Drawing
import numpy as np
import random
from utils import SineWave
import uuid
import itertools

class Carnival(Drawing):

    def __init__(self, out_name, width, height):
        super().__init__(out_name, width, height)
        self.palette = {"red": "#de4040",
                        "yellow": "#e2bf31",
                        "purple": "#a13d90"}
        self.sine = SineWave(0.031792845*self.width, 0.558472292*self.height)
        self.xshift = 0.048933148 * self.width
        self.yshift = 0.022185698 * self.height
        self.line_grad = 0.9
        
    def draw(self):
        self.add_bg(self.palette['yellow'])
        lines = self.create_cut_lines()
        for _ in range(30):
            self.stamp(lines)

    def create_cut_lines(self, num_lines=40):
        top_xs = np.linspace(0, self.width*2, num_lines+1)[1:]
        bottom_xs = top_xs - (self.height/self.line_grad)
        return [[(top_x, 0), (bot_x, self.height)] for top_x, bot_x in zip(top_xs, bottom_xs)]

    def create_random_mask(self, lines):
        num_visible = 5
        indices = random.sample(range(len(lines)-2), num_visible)
        mask_id = f"mask-{uuid.uuid4()}"
        clip = self.dwg.defs.add(self.dwg.clipPath(id=mask_id))
        for i in indices:
            c1, c2 = lines[i]
            c3, c4 = lines[i+2]
            clip.add(self.dwg.polygon([c1, c2, c4, c3]))
        return mask_id
    
    def mask_dwg_add(self, element, mask_id):
        element['clip-path'] = f"url(#{mask_id})"
        self.dwg.add(element)

    def get_wave_points(self):
        wave_points = []
        #trough_x = -random.random()*self.width - 100
        trough_x = -100
        trough_y = 100
        for _  in range(30):
            horizontal_points = self.sine.sample(trough_y, trough_x, 0, self.height)
            wave_points.append([(x,y) for (y,x) in horizontal_points])
            trough_x += self.xshift
            trough_y += self.yshift
        return wave_points
    
    def get_polygons(self, wave_pts, colours):
        assert len(wave_pts)-1 == len(colours)
        group = self.dwg.g()
        for i in range(len(wave_pts)-2):
            group.add(self.dwg.polygon(wave_pts[i] + list(reversed(wave_pts[i+1])), fill=colours[i], stroke=colours[i]))
        return group

    def stamp(self, lines):
        wave_pts = self.get_wave_points()
        #colours = np.array(random.choices(list(self.palette.values()), k=len(wave_pts)-1))

        # Generate colours
        colours = []
        for _ in range(len(wave_pts)-1):
            choices = list(self.palette.values())[:]  # Copy the list of colors
            if len(colours) >= 2 and colours[-1] == colours[-2]:  
                # Remove last color if it appeared twice in a row
                choices.remove(colours[-1])
            colours.append(random.choice(choices))  # Pick a random color from the remaining choices

        group = self.get_polygons(wave_pts, colours)
        self.mask_dwg_add(group, self.create_random_mask(lines))


if __name__ == '__main__':
    drawing = Carnival('out/carnival', 1000, 1.36)
    drawing.render()