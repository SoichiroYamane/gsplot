# 3. Configuration of gsplot

[Configuration](#gsplot.config.config) provides a way to customize default keyword arguments of the functions defined in `gsplot`. This is very useful when you need to plot multiple plots with the same parameters.

The configuration file can be described in json format. Each keyword needs to be referred from functions defined in `gsplot`, and parameters can be passed to the function. At default, `gsplot` will search for the configuration in the following directories:

1. Current working directory: `./gsplot.json`
2. User's configuration directory: `~/.cofig/gsplot/gsplot.json`
3. User's home directory: `~/gsplot.json`

You can also specify the configuration file by using the [gsplot.config_load](#gsplot.config.config.config_load) function.

```{note}
Function that can be configured have a note about passed parameters in api documents.
```

## Priority of Parameters

The priority of the parameters is as follows:

1. Parameters passed to the function
2. Parameters passed to the configuration
3. Default parameters

```{mermaid}
%%{init: {
    "theme": "base", 
    "themeVariables": {
        "primaryColor": "#ffffff", 
        "primaryBorderColor": "#61AFC2",
        "edgeLabelBackground": "#ffffff",
        "tertiaryColor": "#61AFC2"
    },
    "themeCSS": "marker path { fill: #61AFC2 !important; }"
}}%%
graph TD
    linkStyle default stroke:#61AFC2,stroke-width:1;

    Start([Start]) --> A[Parameters passed to the function?]
    A -->|Yes| F[Final Parameters]
    A -->|No| B[Parameters passed to the configuration?]
    B -->|Yes| F
    B -->|No| C[Default parameters]
    C --> F
```

## Example of Axes with Configuration

As a example, we will create a configuration file that sets the default values of the [gsplot.axes](#gsplot.figure.axes.axes). Parameters of [gsplot.axes](#gsplot.figure.axes.axes) are following:

```python
gsplot.axes(store = False, size = [5, 5], unit = "in", mosaic = "A", clear = True, ion = False)
```

If you set the configuration file like this:

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
```

This code is equivalent to the following code:

```python
gsplot.axes(store = True, size = [10, 10], unit = "in", mosaic = "ABC", clear = True, ion = False)
```

## Example

### Main Functions

| Function                                                | A Brief Overview                             |
| :---:                                                   | :-------:                                    |
| [gsplot.config_load](#gsplot.config.config.config_load) | Load configuration file with a specific path |
| [gsplot.config_dict](#gsplot.config.config.config_dict) | Get dictionary of the configuration          |
| [gsplot.config_entry_option](#gsplot.config.config.config_entry_option)                 | Get dictionary of configuration with a specific key                        |

### Configuration

```{literalinclude} ../../../demo/3_config/gsplot.json
```

### Code

```{literalinclude} ../../../demo/3_config/config.py
```

### Plot

```{image} ../../../demo/3_config/config.png
:alt: config
:class: bg-primary
:width: 500px
:align: center
```

### Output

```bash
config_dict:
{
    'rich': {'traceback': {}},
    'rcParams': {'xtick.major.pad': 6, 'ytick.major.pad': 6},
    'axes': {'ion': True, 'size': [15.0, 5.0], 'unit': 'in', 'clear': True, 'mosaic': 'ABC'},
    'show': {'show': True}
}

axes_config:
{'ion': True, 'size': [15.0, 5.0], 'unit': 'in', 'clear': True, 'mosaic': 'ABC'}
(gsplot-py3.13) root@e985553428b2:~/opt/demo/3_config# python config.py

config_dict:
{
    'rich': {'traceback': {}},
    'rcParams': {'xtick.major.pad': 6, 'ytick.major.pad': 6},
    'axes': {'ion': False, 'size': [15.0, 5.0], 'unit': 'in', 'clear': False, 'mosaic': 'ABC'},
    'show': {'show': True}
}

axes_config:
{'ion': False, 'size': [15.0, 5.0], 'unit': 'in', 'clear': False, 'mosaic': 'ABC'}
```
