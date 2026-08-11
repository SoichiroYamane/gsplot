from pprint import pprint

import gsplot as gs

# Configuration loading is explicit and returns an immutable value object.
config = gs.load_config("./gsplot.json")

print("configuration:")
pprint(config.as_mapping())

# Direct arguments override values from the configuration file.
fig, axes = gs.subplots(config=config, mosaic="A")
axis = axes["A"]
gs.line(axis, [0, 1, 2], [0, 1, 4], props={"label": "configured line"})
gs.legend(axis)
gs.savefig(fig, "config", show=False, overwrite=True)
