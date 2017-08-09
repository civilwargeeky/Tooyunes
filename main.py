import updater
from log import log

#No matter what, we have to make sure TCL and TK can be found
from os import environ, getcwd, path
if path.exists("lib"):
  environ["TCL_LIBRARY"] = path.join(getcwd(), "lib", "tcl8.6")
  environ["TK_LIBRARY"]  = path.join(getcwd(), "lib", "tk8.6")

#Returns false if the program should abort, true otherwise
def checkUpdates():
  if updater.checkInstall() == False: #Signals we have no internet
    return False
  
  if updater.updateProgram(): #If this returns true, an update is in progress so we should exit
    log.info("Main exiting")
    return False
  return True


def main():  
  import mainDisplay
  #mainDisplay.main()
  
  
if __name__ == "__main__":
  try:
    checkUpdates()
  except RuntimeError: #Raised when the internet fails
    import sys
    sys.exit()
  #After updates go into main
  main()