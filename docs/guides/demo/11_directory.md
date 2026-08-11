# 11. Directory

`gsplot` provides small helpers for inspecting the current working directory,
the user's home directory, and the directory containing the executed main
script. `pwd_move()` re-enters the current working directory; it is useful as a
simple path helper but does not change to the home directory.

## Example

### Code

```{literalinclude} ../../../demo/11_directory/directory.py
```
