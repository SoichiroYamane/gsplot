import gsplot as gs
import matplotlib.pyplot as plt

x = [1, 2, 3, 4, 5]
y = [1, 2, 3, 4, 5]

fig, axs = plt.subplots(2, 2, figsize=(10, 10))

axs[0, 0].plot(x, y)
gs.line(
    axs[0, 1],
    x,
    y,
)

gs.label([["x", "y"], ["x", "y"], ["x", "y"], ["x", "y"]])

plt.show()
plt.savefig("subplots.png")
