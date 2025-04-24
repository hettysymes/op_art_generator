class ElemRef:

    def __init__(self, polyline_node):
        self.polyline_node = polyline_node
        self.node_type = polyline_node.node_info().name
        self.node_id = polyline_node.node_id
        self.reversed = False

    def reverse(self):
        self.reversed = not self.reversed

    def get_base_points(self):
        return self.polyline_node.compute()[0].get_points()

    def get_points(self):
        points = self.get_base_points()
        if self.reversed:
            return list(reversed(points))
        return points

