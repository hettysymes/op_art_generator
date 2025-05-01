from abc import ABC, abstractmethod

import cairosvg
import svgwrite

from ui.nodes.utils import process_rgb


class Drawing(ABC):

    def __init__(self, out_name, height, wh_ratio):
        self.out_name = out_name
        self.height = height
        self.width = wh_ratio * height
        self.dwg = svgwrite.Drawing(f'{out_name}.svg', size=(self.width, self.height))
        self.scaled_elem = None

        # Define clipping that clips everything outside of view box
        clip = self.dwg.defs.add(self.dwg.clipPath(id="viewbox-clip"))
        clip.add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height)))

    # Add element to drawing whilst clipping parts outside the view box
    def dwg_add(self, element):
        element['clip-path'] = "url(#viewbox-clip)"
        self.dwg.add(element)

    def add_bg(self, colour=(255, 255, 255, 255)):
        fill, fill_opacity = process_rgb(colour)
        self.dwg_add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height), fill=fill, fill_opacity=fill_opacity))

    def save_both(self):
        self.dwg.save()
        cairosvg.svg2png(url=f"{self.out_name}.svg", write_to=f"{self.out_name}.png")

    def render(self):
        self.draw()
        self.save_both()
        print("SVG and PNG files saved.")

    def save(self):
        self.draw()
        self.dwg.save()
        return self.dwg.filename, self.scaled_elem

    @abstractmethod
    def draw(self):
        pass
