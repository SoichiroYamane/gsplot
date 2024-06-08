from ..color.colormap import Colormap


class NumLines:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(NumLines, cls).__new__(cls)
            cls._instance._num_lines = 0
        return cls._instance

    @property
    def num_lines(self):
        return self._num_lines

    def increment(self):
        self._num_lines += 1

    @classmethod
    def count(cls, func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            cls().increment()
            return result

        return wrapper

    @classmethod
    def reset(cls):
        cls._instance = None


class AutoColor:
    def __init__(self):
        self.COLORMAP_LENGTH = 5
        self.CMAP = "viridis"
        self.colormap = Colormap(
            cmap=self.CMAP, N=self.COLORMAP_LENGTH
        ).get_split_cmap()

        self.num_lines = NumLines().num_lines
        self.cycle_color_index = self.num_lines % self.COLORMAP_LENGTH

    def get_color(self):
        return self.colormap[self.cycle_color_index]
