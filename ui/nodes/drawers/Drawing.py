from abc import ABC, abstractmethod

import cairosvg
import svgwrite

from ui_old.nodes.utils import process_rgb


class Drawing(ABC):

    def __init__(self, filepath, width, height):
        self.width = width
        self.height = height
        self.dwg = svgwrite.Drawing(filepath, size=(self.width, self.height))

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

    @abstractmethod
    def draw(self):
        pass
