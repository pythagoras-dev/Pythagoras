class PythagorasException(Exception):
    def __init__(self, message):
        self.message = message

class NotPicklableObject(PythagorasException):
    def __init__(self, message):
        PythagorasException.__init__(self, message)


class NonCompliantFunction(PythagorasException):
    def __init__(self, message):
        PythagorasException.__init__(self, message)