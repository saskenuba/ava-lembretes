class AssignmentExpired(Exception):
    """
    Assignment is over.
    """

    def __init__(self, msg=None):
        "docstring"
        self.msg = msg
