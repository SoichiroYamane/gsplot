from pathlib import Path

import gsplot as gs

print("current directory:", Path.cwd())
print("home directory:", Path.home())

# Canonical gsplot operations receive paths explicitly; they do not change cwd.
print("package metadata:", gs.build_info())
