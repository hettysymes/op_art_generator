from Drawing import Drawing
from Warp import PosWarp
import numpy as np

class CantusFirmus(Drawing):

    def __init__(self, out_name, width, height):
        super().__init__(out_name, width, height)
        
    def draw(self):
        self.add_bg()

if __name__ == '__main__':
    drawing = CantusFirmus('out/cantus_firmus', 1000, 0.89)
    drawing.render()