import numpy as np

import gsplot as gs

config = gs.load_config("./gsplot.json")
names = ["A1g", "A2u", "B1g", "B1u"]
fig, axes = gs.subplots("AB", config=config)
colors = gs.sample_cmap("plasma", count=len(names))

for index, name in enumerate(names):
    data = gs.read(
        f"../data/gap/Gapeq_{name}.dat",
        skip_header=1,
        delimiter="\t",
    )
    options = {"c": colors[index], "label": name, "lw": 2}
    gs.line(axes["A"], data[0], data[1], **options)
    gs.line(axes["B"], data[0], np.sqrt(data[1]), **options)

gs.legend(axes)
gs.style_axes(axes, gs.AxisSpec(xlabel="T/Tc", ylabel="value"))
gs.savefig(fig, "SC_cal", show=False, overwrite=True)
