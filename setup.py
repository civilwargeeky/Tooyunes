from distutils.core import setup
import py2exe
import shutil
from os import chdir
from os.path import join
from subprocess import check_output
from sys import argv, path
from time import sleep


#If the argument is present, returns true and removes it from the arguments list
def getArg(arg):
  if arg in argv:
    argv.pop(argv.index(arg))
    return True
  return False
  
def log(*arg, **kwarg):
  return print("[BUILD]", *arg, **kwarg)
  
def debug(*arg, **kwarg):
  if DEBUG:
    return print("[DEBUG]", *arg, **kwarg)

DEBUG = getArg("--debug") #Check if we are in debug
OUTPUT_FOLDER   = "build"
INNO_SETUP_PATH = '"C:\Program Files (x86)\Inno Setup 5\Compil32.exe"'

if not DEBUG:
  log("Updating youtube-dl")
  output = check_output("src\\resources\\youtube-dl.exe -U").decode("utf-8")
  if "up-to-date" in output:
    log("Youtube-DL up to date!")
  else:
    log("Waiting 5 for file handle to close")
    sleep(5)

VERSION = None
try:
  with open("version.txt") as file:
    VERSION = file.read()
except FileNotFoundError:
  pass
finally:
  VERSION = VERSION or "0.0.0"
  debug("Previous version: ", VERSION)


#All the version updating code
if not DEBUG: #If a release, we should increment the version number
  v = [int(i) for i in VERSION.split(".")]
  if len(v) != 3:
    raise RuntimeError("Version number had {} parts, 3 expected".format(len(v)))
  if getArg("--major"): #Increment major version, leave others
    v = [v[0]+1, 0, 0] 
  elif getArg("--minor"):
    v = [v[0], v[1]+1, 0]
  else:
    v[2] += 1
  VERSION = ".".join([str(i) for i in v])
  log("New VERSION:",VERSION)
  with open("version.txt", "w") as file:
    file.write(VERSION)

log("Starting build process")
#Do all the actual building
path.append("src") #Allows all modules in this folder to be imported
setup(**{
  "name": "Tooyunes",
  "version": VERSION,
  "description": "Downloads music from youtube using youtube-dl",
  "author": "DJ Dan",
  "data_files": [(".", ["C:/Windows/System32/msvcr100.dll"])] + \
    [] if not getArg("--big") else [("resources", ["src/resources/"+i for i in ("youtube-dl.exe", "ffprobe.exe", "ffmpeg.exe")])],
  "options": {"py2exe":{
    "dist_dir": OUTPUT_FOLDER,
    "compressed": (not DEBUG), #If not debug, compress the exe to make it smaller
    "includes": ["imp"],
    #"dll_includes": ["MSVCR100.dll"],
    "excludes": ["pydoc", "doctest", "inspect"],
    "bundle_files": (3 if DEBUG else 2),
    }
  },
  ("console" if DEBUG else "windows"): [{
    "script": "src/main.py",
    "icon_resources": [(1, "src/img/mainIcon.ico")],
    "version": VERSION + ".0" #Because windows version has 4 parts
  }]
})

#Remove this folder as it is gigantic and unneeded
#For whatever reason, having pillow includes this
shutil.rmtree(join("build","tcl"))

#Now make the installer
if not DEBUG:
  from os import system
  log("Running Inno Setup File")
  system(INNO_SETUP_PATH+' /cc Tooyunes.iss')