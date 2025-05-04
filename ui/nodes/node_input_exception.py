class NodeInputException(Exception):
    """Custom exception for invalid node inputs."""

    def __init__(self, message, node_id):
        self.node_id = node_id
        self.message = message
        self.title = "Node Input Error"
        super().__init__(self.message)
