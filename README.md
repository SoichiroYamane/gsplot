# gsplot

Welcome to **gsplot** (general-scientific plot), a toolkit designed to enhance the capabilities of data visualization based on `matplotlib`. This package is specifically tailored for creating high-quality figures in the scientific field. It provides a range of utilities for managing plots, including customization of legends, handling colormaps, managing axis properties, and more.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
  - [Basic Usage](#basic-usage)
  - [Advanced Features](#advanced-features)
- [Modules](#modules)
  - [Axes Management](#axes-management)
  - [Colormap Handling](#colormap-handling)
  - [Legends](#legends)
  - [Ticks](#ticks)
- [Contributing](#contributing)
- [License](#license)

## Installation

To use **Project Name**, ensure that you have `Python 3.7+` installed. You can install the package using `pip`:

needs to be updated on python version

```bash
pip install gsplot
```

Make sure you have the required dependencies listed in `requirements.txt`, which typically include `matplotlib`, `numpy`.

## Usage

### Basic Usage

Below is a quick example of how to use some of the basic features of **gsplot**:

```python
import gsplot as gs

# Create list of axes
axes = gs.axes(
  store = True,
  size=[8, 8],
  mosaic = "AB;CD",
)

# plot a line on the first axis: corresponding to A
gs.line(
    axis_index=0,
    xdata=[1, 2, 3],
    ydata=[1, 1, 1],
)

gs.label(
    [
        ["$A_x$","$A_y$"],
        ["$B_x$","$B_y$"],
        ["$C_x$","$C_y$"],
        ["$D_x$","$D_y$"],
    ]
)
gs.show()

```

The output is shown below:
[![alt](pictures/figure.png =250x)](href "Basic Usage of gsplot")

### Advanced Features

**gsplot** offers advanced customization options for your plots:

- **Colormaps**: Easily apply colormaps to your lines and scatter plots.
- **Custom Legends**: Create legends with custom handlers, including colormaps.
- **Axis Management**: Control the appearance and behavior of axes, including aspect ratios, ticks, and labels.
- **Plot Configuration**: Customize your plot style in `~/.gsplot.json`.

#### Example: Configuration of gsplot

Place the following configuration in `~/.gsplot.json`. More details can be found [here](xxx).

```json
{
  "rcParams": {
    "xtick.major.pad": 6,
    "ytick.major.pad": 6,
    "backends": "MacOSX"
  },
  "load": {
    "unpack": true
  },
  "axes": {
    "ion": true,
    "size": [
      5.0,
      3.0
    ],
    "unit": "in",
    "clear": true
  },
  "show": {
    "show": true
  },
  "labels": {
    "add_index": true,
    "tight_layout": true
  },
  "line": {
    "ms": 10
  },
  "legend": {
    "loc": "upper right"
  },
}
```

## Modules

... to be updated

## Authors

- Giordano Mattoni
- Soichiro Yamane

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
