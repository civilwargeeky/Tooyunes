import json
import tkinter as tk
from urllib.request import urlopen #For update checking


def main():
  #CONSTANTS
  UPDATE_LINK = "https://api.github.com/repos/civilwargeeky/Tooyunes/releases/latest"
  VERSION_FILE = "version.txt"

  #First thing we do is check for updates
  try: #Get our version so we see if we need to update
    with open(VERSION_FILE) as file:
      version_current = file.read()
  except:
    version_current = None
    
  try:
    with urlopen(UPDATE_LINK) as response:
      updateData = json.loads(response.read().decode("utf-8"))
      if updateData["tag_name"] != version_current: #The tag should be the released version
        fileData = updateData["assets"][0]
        try:
          with open(fileData["name"], "wb") as file:
            with urlopen(fileData["browser_download_url"]) as webfile:
              file.write(webfile.read())
          import subprocess
          subprocess.Popen(fileData["name"]) #Call this file and then exit the program
          return
        except ValueError:
          pass
    return
  except OSError: #Error in getting the url
    pass #Report the error to the user
  except (ValueError, UnicodeDecodeError): #Error in parsing input
    pass #Report the error to the user
  except KeyError: #Data is not formatted like we expect it to be
    pass
  except IndexError: #No binary attached to release -- no assets (probably)
    pass
  
  root = tk.Tk()
  root.title("Title")
  root.mainloop()
  
  
  
if __name__ == "__main__":
  main()