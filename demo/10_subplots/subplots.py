import matplotlib.pyplot as plt

import gsplot as gs

x = [1, 2, 3, 4, 5]
y = [1, 2, 3, 4, 5]

# Create subplots
fig, axs = plt.subplots(2, 2, figsize=(8, 8))

axs[0, 0].plot(x, y)

# gsplot can be used to plot on the subplots
gs.line(
    axs[0, 1],
    x,
    y,
)
gs.label([["x", "y"], ["x", "y"], ["x", "y"], ["x", "y"]])

# Needs to save the figure
plt.savefig("subplots.png")
plt.show()
