# 3. Configuration of gsplot

[Configuration](#gsplot.config.config) provides a way to customize default keyword arguments of the functions defined in `gsplot`. This is very useful when you need to plot multiple plots with the same arguments.

The configuration file can be described in json format. Each keyword needs to be referred from functions defined in `gsplot`, and arguments can be passed to the function. `gsplot` will search for the configuration in the following directories:

1. Current working directory: `./gsplot.json`
2. User's configuration directory: `~/.cofig/gsplot/gsplot.json`
3. User's home directory: `~/gsplot.json`

The priority of the arguments is as follows:

1. Arguments passed to the function
2. Arguments passed to the configuration
3. Default arguments

## Example of Axes with Configuration

As a example, we will create a configuration file that sets the default values of the [gsplot.axes](#gsplot.figure.axes.axes). Arguments of [gsplot.axes](#gsplot.figure.axes.axes) are following:

```python
gsplot.axes(store = False, size = [5, 5], unit = "in", mosaic = "A", clear = True, ion = False)
```

If you set the configuration file as follows:

```json
{
  "axes" : {
    "size" : [10, 10],
    "mosaic" : "AB"
  }
}
```

And place this configuration file in the proper directory, you can create a plot with the following code:

```python
gsplot.axes(store= True, mosaic = "ABC")

# This function is equivalent to
# gsplot.axes(store = True, size = [10, 10], unit = "in", mosaic = "ABC", clear = True, ion = False)
```

## Example of Plot with Configuration

### Configuration

```{literalinclude} ../../../demo/3_config/gsplot.json
```

### Plot

```{literalinclude} ../../../demo/3_config/config.py
```

```{image} ../../../demo/3_config/config.png
:alt: config
:class: bg-primary
:width: 500px
:align: center
```
