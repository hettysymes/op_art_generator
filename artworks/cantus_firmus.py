from ui.nodes.drawers.Drawing import Drawing
import numpy as np

class IntensityPicker:

    def __init__(self, f):
        self.f = f
    
    def get_grey(self, i):
        intensity = max(0, min(255, int(self.f(i))))
        return f"#{intensity:02X}{intensity:02X}{intensity:02X}"

class CantusFirmus(Drawing):

    def __init__(self, out_name, width, height):
        super().__init__(out_name, width, height)
        self.grey_picker = lambda i: np.interp(i, [0.056, 0.649, 0.956], [174, 61, 187])
        self.colour_palette = ['#c4cb3a', '#d38aaa', '#7dbbd3', '#3c3c3c', IntensityPicker(self.grey_picker), '#f5f9f4']
        self.gradual_colours = [self.colour_palette[0],
                              self.colour_palette[1],
                              self.colour_palette[2]]
        self.gradual_widths = np.array([0.00393, 0.00432, 0.00533]) * self.width
        self.peak_colours = [self.colour_palette[3], self.colour_palette[4], self.colour_palette[5]]
        self.peak_widths = np.array([0.01771, 0.013, 0.013]) * self.width
        
    def draw(self):
        self.add_bg()
        x = 0
        while x < self.width:
            for i in range(len(self.peak_colours)):
                x = self.draw_block(x, self.gradual_colours, self.gradual_widths)
                x = self.draw_stripe(x, self.peak_colours[i], self.peak_widths[i])
                x = self.draw_block(x, list(reversed(self.gradual_colours)), self.gradual_widths)

    def draw_stripe(self, x, colour, width):
        if isinstance(colour, IntensityPicker):
            colour = colour.get_grey(x/self.width)
        self.dwg_add(self.dwg.rect(
                        insert=(x, 0),
                        size=(width, self.height),
                        fill=colour,
                        ))
        return x + width

    def draw_block(self, x, colours, widths):
        for i in range(len(colours)):
            x = self.draw_stripe(x, colours[i], widths[i])
        return x


if __name__ == '__main__':
    drawing = CantusFirmus('out/cantus_firmus', 1000, 0.89)
    drawing.render()