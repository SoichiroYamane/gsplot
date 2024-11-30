import gsplot as gs
from rich import print

config = gs.config_load("./gsplot.json")

# Check the configuration
config_dict = gs.config_dict()
print(config_dict)

axes_config = gs.config_entry_option("axes")
print(axes_config)

# Create a figure with the configuration
# Priority of the configuration
# 1. Direct arguments to the function
# 2. Configuration file
# 3. Default values
axes = gs.axes(size=[5, 5], mosaic="A")
