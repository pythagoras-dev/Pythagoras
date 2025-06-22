class PythagorasException(Exception):
    def __init__(self, message):
        self.message = message


class NonCompliantFunction(PythagorasException):
    def __init__(self, message):
        PythagorasException.__init__(self, message)