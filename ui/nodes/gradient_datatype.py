import uuid

from ui.nodes.prop_defs import PropValue, PropType, PT_Gradient, List, PT_GradOffset, Point
from ui.nodes.utils import process_rgb


class Gradient(PropValue):

    def __init__(self, start_coord: Point, end_coord: Point, stops: List[PT_GradOffset]):
        super().__init__()
        self.start_coord = start_coord
        self.end_coord = end_coord
        self.stops = stops # Assume this is sorted by ascending offset

    def get(self, dwg):
        grad_id = str(uuid.uuid4())
        gradient = dwg.linearGradient(id=grad_id, start=self.start_coord, end=self.end_coord)
        for stop in self.stops:
            gradient.add_stop_color(offset=stop.offset, opacity=stop.colour.opacity, color=stop.colour.fill)
        dwg.defs.add(gradient)
        return f'url(#{grad_id})'

    @property
    def type(self) -> PropType:
        return PT_Gradient()
