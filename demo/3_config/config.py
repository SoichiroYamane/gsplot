from rich import print

import gsplot as gs

# gsplot provides a configuration file to set the default values of the plot
# gsplot will search for the configuration file in the following locations:
# 1. Current directory: ./gsplot.json
# 2. User config directory: ~/.config/gsplot/gsplot.json
# 3. Home directory: ~/gsplot.json
#
# You can also specify the configuration file path with the `config_load` function
config = gs.config_load(r"./gsplot.json")

# Check the configuration
config_dict = gs.config_dict()
print("\nconfig_dict:", config_dict)

axes_config = gs.config_entry_option("axes")
print("\naxes_config:", axes_config)

# Create a figure with the configuration
# Priority of the configuration
# 1. Direct arguments to the function
# 2. Configuration file
# 3. Default values
axes = gs.axes(store=True, size=[5, 5], mosaic="A")

gs.show("config")
