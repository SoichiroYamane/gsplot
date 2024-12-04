import gsplot as gs

# Get the current working directory
pwd = gs.pwd()
print("pwd: ", pwd)

# Move to the home directory
gs.pwd_move()

# Get the home directory
home = gs.home()
print("home: ", home)

# Move to the main directory
pwd_main = gs.pwd_main()
print("Main directory: ", pwd_main)
