from abc import ABC, abstractmethod
import svgwrite


class Drawing(ABC):

    def __init__(self, filepath, width, height):
        self.width = width
        self.height = height
        self.dwg = svgwrite.Drawing(filepath, size=(self.width, self.height), preserveAspectRatio="none")

        # Define clipping that clips everything outside of view box
        clip = self.dwg.defs.add(self.dwg.clipPath(id="viewbox-clip"))
        clip.add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height)))

    # Add element to drawing whilst clipping parts outside the view box
    def dwg_add(self, element):
        element['clip-path'] = "url(#viewbox-clip)"
        self.dwg.add(element)

    def save(self):
        self.draw()
        self.dwg.save()

    @abstractmethod
    def draw(self):
        pass
