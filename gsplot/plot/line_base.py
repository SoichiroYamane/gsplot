from ..color.colormap import Colormap


class NumLines:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(NumLines, cls).__new__(cls)

            cls._instance._num_lines = [0]
        return cls._instance

    def updata_num_lines(self, axis_index: int):
        length = len(self._num_lines)
        if axis_index + 1 > length:
            for i in range(axis_index - length + 1):
                self._num_lines.append(0)

    @property
    def num_lines(self):
        return self._num_lines

    def num_lines_axis(self, axis_index: int):
        self.updata_num_lines(axis_index)
        return self._num_lines[axis_index]

    def increment(self, axis_index: int):
        self.updata_num_lines(axis_index)
        self._num_lines[axis_index] += 1

    @classmethod
    def count(cls, func):
        def wrapper(self, *args, **kwargs):
            cls().increment(self.axis_index)
            result = func(self, *args, **kwargs)
            return result

        return wrapper

    @classmethod
    def reset(cls):
        cls._instance = None


class AutoColor:
    def __init__(self, axis_index: int):
        self.COLORMAP_LENGTH = 5
        self.CMAP = "viridis"
        self.colormap = Colormap(
            cmap=self.CMAP, N=self.COLORMAP_LENGTH
        ).get_split_cmap()

        self.num_lines_axis = NumLines().num_lines_axis(axis_index)
        self.cycle_color_index = self.num_lines_axis % self.COLORMAP_LENGTH

    def get_color(self):
        return self.colormap[self.cycle_color_index]
