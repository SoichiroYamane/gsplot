class Test:
    def __init__(self):
        self._a = 1
        self.b = 2

    def get_a(self):
        return self._a

    def set_a(self, value):
        self._a = value

    a = property(get_a, set_a)


def pp_a():
    print("oni")
