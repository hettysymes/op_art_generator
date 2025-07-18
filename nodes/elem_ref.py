class ElemRef:

    def __init__(self, node):
        self.node = node
        self.node_type = node.node_info().name
        self.node_id = node.node
        self.reversed = False
        self.deletable = False

    def is_deletable(self):
        return self.deletable

    def set_deletable(self, deletable):
        self.deletable = deletable

    def reverse(self):
        self.reversed = not self.reversed

    def compute(self):
        return self.node.compute()

    def get_base_points(self):
        shape, transform_list = self.compute().shape_transformations()[0]
        return shape.get_points(transform_list)

    def get_points(self):
        points = self.get_base_points()
        if self.reversed:
            return list(reversed(points))
        return points
