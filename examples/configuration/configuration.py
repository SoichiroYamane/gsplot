from pprint import pprint

import gsplot as gs

# Configuration loading is explicit and returns an immutable value object.
config = gs.load_config("./gsplot.json")

print("configuration:")
pprint(config.as_mapping())

# Direct arguments override values from the configuration file.
fig, axes = gs.subplots("A", config=config)
axis = axes["A"]
gs.line(axis, [0, 1, 2], [0, 1, 4], label="configured line")
gs.legend(axis)
gs.save(fig, "config", show=False)
