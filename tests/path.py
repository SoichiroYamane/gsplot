import os

test = os.getcwd()

program_direc = os.path.dirname(os.path.abspath("__file__"))

print(test, program_direc)
