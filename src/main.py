import msgBox, updater
from log import log

#Returns false if the program should abort, true otherwise
def checkUpdates():
  try:
    updater.checkInstall()
  except RuntimeError:  #Signals we have no internet
    msgBox.errorBox("No internet, cannot update.\nClosing Program")
    return False
  
  if updater.updateProgram(): #If this returns true, an update is in progress so we should exit
    log.info("Main exiting")
    return False
  return True


def main():  
  import mainDisplay
  mainDisplay.main("Title")
  
  
if __name__ == "__main__":
  if checkUpdates():
    main()
  