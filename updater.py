#This file deals with updating the installation
import json, os, subprocess
from io import BytesIO
from shutil import copyfileobj
from urllib.request import Request, urlopen
from zipfile import ZipFile
join = os.path.join #Alias for time saving

from log import log
from msgBox import questionBox, FileDLProgressBar

#CONSTANTS
UPDATE_LINK = "https://api.github.com/repos/civilwargeeky/Tooyunes/releases/latest"
FFMPEG_LINK = "http://ffmpeg.zeranoe.com/builds/win64/static/ffmpeg-3.3.2-win64-static.zip"
YT_DL_LINK  = "https://yt-dl.org/downloads/latest/youtube-dl.exe"

UPDATE_FILE = "Updater.exe"

#Checks if this is a first-time installation (we need to install ffmpeg, ffprobe, and youtube-dl)
#NOTE ON ERRORS: We do not check for internet errors, because if we don't have internet here, we can't do anything
def checkInstall():
  if not os.path.isdir("resources"):
    os.mkdir("resources")
    
  progress = FileDLProgressBar("Performing first-time installation. Please wait")
    
  #Do youtube check ahead of time in order to make good indicator box
  ytNeeded = not os.path.exists(join("resources", "youtube-dl.exe"))
  if ytNeeded:
    progress.add("Downloading youtube-dl.exe", "Done!")
  
  fileList = ["ffmpeg.exe", "ffprobe.exe"]
  for file in fileList:
    if not os.path.exists(join("resources",file)):
      progress.addStart("Downloading ffmpeg .zip file (this one can take a while)", *["Writing " + i for i in fileList])
      progress.start()
      log.warning("Resources file:", file,"does not exist, downloading")
      #Well great, now we have to download and parse the zip file
      zipURL = Request(FFMPEG_LINK,
        headers = {"User-Agent": "Python Agent"} #Apparently the agent just has to exist
        )
      with urlopen(zipURL) as response:
        log.debug("Writing response to Bytes")
        dlZip = ZipFile(BytesIO(response.read()))
        log.debug("File downloaded")
      for descriptor in dlZip.namelist():
        file = os.path.basename(descriptor)
        if file in fileList:
          progress.next() #Go to the next progress bar action
          log.debug("Found file:", descriptor)
          fileList.pop(fileList.index(file))
          with dlZip.open(descriptor) as source, open(join("resources", file), "wb") as dest:
            copyfileobj(source, dest)
          log.debug("File write successful")
      break
  if ytNeeded:
    progress.start()
    log.warning("Resources file: youtube-dl.exe does not exist, downloading")
    with urlopen(YT_DL_LINK) as source, open(join("resources", "youtube-dl.exe"), "wb") as dest:
      copyfileobj(source, dest)
    log.debug("Write Success")
    progress.next() #Say "Done!"
  progress.close()

#Downloads a new program installer if the github version is different than ours
#Returns true on successful update (installer should be running), false otherwise
def updateProgram():
  try:
    if os.path.exists(UPDATE_FILE):
      os.remove(UPDATE_FILE)
  except PermissionError:
    log.error("Cannot remove installer exe, must be open still")
    return False
  
  try: #Get our version so we see if we need to update
    with open("version.txt") as file:
      versionCurrent = file.read()
      log.debug("Current Version:", versionCurrent)
  except:
    versionCurrent = None
    log.warning("Version file not found")
    
  try:
    log.info("Beginning update check")
    with urlopen(UPDATE_LINK) as response:
      updateData = json.loads(response.read().decode("utf-8"))
      newVersion = updateData["tag_name"]
      log.debug("Good data received")
      log.debug("Most Recent:", newVersion,"| Our Version:", versionCurrent)
      if newVersion != versionCurrent: #The tag should be the released version
        if questionBox("Version "+newVersion+" now available! Would you like to update?", title="Update"):
          log.info("Updating to version", newVersion)
          fileData = updateData["assets"][0]
          webAddress = fileData["browser_download_url"]
          with urlopen(webAddress) as webfile, open(fileData["name"], "wb") as file:
            log.debug("Downloading new file from", webAddress)
            #Both file and webfile are automatically buffered, so this is fine to do
            copyfileobj(webfile, file)
          subprocess.Popen(fileData["name"]) #Call this file and then exit the program
          return True
        else:
         log.info("User declined update")
         
      else:
        log.info("We have the most recent version")
  except OSError as e: #Error in getting the url
    #only warning because this means they are likely not connected to the internet
    log.warning("File download error!", exc_info = e) 
  except IndexError: #No binary attached to release -- no assets (probably)
    log.error("No binary attached to most recent release!")
  except Exception as e:
    log.error("Error in update!", exc_info = e) #Log the error
  #If we did not return in the function, we did not update properly
  return False
  
  
def updateYoutubeDL():
  log.info("Updating Youtube-DL")