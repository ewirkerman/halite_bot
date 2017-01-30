from subprocess import call
from glob import glob
import os

# cd to the script directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# look for the pypy executable
pypybin = glob('pypy*/bin/pypy')
if len(pypybin) == 0:
    # if it isn't found we're probably running locally
    pypybin = 'python'
else:
    pypybin = pypybin[0]

pypybin = "C:\Progra~2\pypy\pypy.exe"
# call the script with the relative path to pypy
call(pypybin + " ./pypyBot.py", shell=True)
