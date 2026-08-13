import gsplot as gs

# Canonical gsplot operations receive paths explicitly; they do not change the
# caller's directory or inspect machine-specific path state.
print("package metadata:", gs.build_info())
