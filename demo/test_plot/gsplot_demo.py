import numpy as np

import gsplot as gs

config = gs.load_config("./gsplot.json")
names = ["A1g", "A2u", "B1g", "B1u"]
fig, axes = gs.subplots(config=config, mosaic="AB")
colors = gs.sample_cmap("plasma", count=len(names))

for index, name in enumerate(names):
    data = gs.read_array(
        f"../data/gap/Gapeq_{name}.dat",
        options={"skip_header": 1, "delimiter": "\t", "unpack": True},
    )
    props = {"color": colors[index], "label": name, "linewidth": 2}
    gs.line(axes["A"], data[0], data[1], props=props)
    gs.line(axes["B"], data[0], np.sqrt(data[1]), props=props)

gs.legends(fig)
gs.style_axes(axes, gs.AxisSpec(xlabel="T/Tc", ylabel="value"))
gs.savefig(fig, "SC_cal", show=False, overwrite=True)
