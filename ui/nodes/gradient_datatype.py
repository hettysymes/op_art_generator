import uuid

from ui.nodes.utils import process_rgb


class Gradient:
    def __init__(self, start_col, stop_col):
        super().__init__()
        self.start_col = start_col
        self.stop_col = stop_col

    def get(self, dwg):
        fill1, opacity1 = process_rgb(self.start_col)
        fill2, opacity2 = process_rgb(self.stop_col)
        grad_id = uuid.uuid4()
        gradient = dwg.linearGradient(id=grad_id, start=(0, 0), end=(1, 0))  # From left to right
        gradient.add_stop_color(offset=0, opacity=opacity1, color=fill1)  # Start with transparent
        gradient.add_stop_color(offset=1, opacity=opacity2, color=fill2)  # End with white
        dwg.defs.add(gradient)
        return f'url(#{grad_id})'