from abc import ABC, abstractmethod

from ui.nodes.drawers.error_drawer import ErrorDrawer


class Visualisable(ABC):

    @abstractmethod
    def save_to_svg(self, filepath, width, height):
        pass


class MatplotlibFig(Visualisable):
    DPI = 100

    def __init__(self, fig):
        self.fig = fig

    def save_to_svg(self, filepath, width, height):
        self.fig.set_size_inches(width / MatplotlibFig.DPI, height / MatplotlibFig.DPI)
        self.fig.set_dpi(MatplotlibFig.DPI)
        self.fig.savefig(filepath, format='svg', bbox_inches='tight')

class ErrorFig(Visualisable):

    def __init__(self, title, content):
        self.title = title
        self.content = content

    def save_to_svg(self, filepath, width, height):
        ErrorDrawer(filepath, width, height, (self.title, self.content)).save()