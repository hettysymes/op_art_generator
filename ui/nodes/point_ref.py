class PointRef:

    def __init__(self, polyline_node):
        self.node_type = polyline_node.node_info().name
        self.node_id = polyline_node.node_id
        self.points = polyline_node.compute()[0].get_points()
        self.reversed = False

    def reverse(self):
        self.reversed = not self.reversed

    def get_points(self):
        if self.reversed:
            return list(reversed(self.points))
        return self.points

