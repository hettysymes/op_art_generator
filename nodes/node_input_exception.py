class NodeInputException(Exception):
    """Custom exception for invalid node inputs."""

    def __init__(self, message):
        self.message = message
        self.title = "Node Input Error"
        super().__init__(self.message)
