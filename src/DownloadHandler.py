import json, io, subprocess, re, os, threading, logging
from mutagen.easyid3 import EasyID3
from concurrent.futures import ThreadPoolExecutor

# NOTE: FOR FUTURE https://github.com/ytdl-org/youtube-dl/#embedding-youtube-dl
# This module should only handle downloading the videos and putting them in the cache, updating the data store

import Settings

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

#This will be an object that handles inheritance, getting and setting in a sane way, etc.
settings = Settings.youtubeSettings
settings.updateDefaults({
  "concurrentDownloads": 10,
  "youtube_dl": r"resources\youtube-dl.exe",
  "pipeOptions": {"text": True, "stderr": subprocess.STDOUT},
  "formatString": "%(id)s.%(ext)s",
  "youtubeWait": 5, # Time in between each call to youtube.com
  "youtubeSettings": {},
})

class TimedLock:
  """ 
  This is a lock that you only need to acquire, and will automatically free after a timer
  The point of this is that we should have a certain amount of time in between requests to youtube to prevent being rate limited
  """

  def __init__(self, timeout: float):
    """
    timeout: the time after the lock is acquired that it will be released, in seconds
    """
    self.lock = threading.Lock()
    self.timeout = timeout

  def setTime(self, timeout):
    self.timeout = timeout

  def acquire(self, *args, **kwargs):
    if self.timeout > 0:
      if self.lock.acquire(*args, **kwargs): # This statement will wait until the lock has been acquired
        log.debug("Lock acquired. Waiting {} seconds before next call".format(self.timeout))
        threading.Timer(self.timeout, self.lock.release).start() # After a given timer, releases the underlying lock
        return True # If we succeed in acquiring the lock, start a timer to release the lock
      return False # If we fail at acquiring the lock, don't do anything else
    return True # If there is no timeout, we always succeed


class VideoProcessor:

  def __init__(self, storageFolder="_VideoStore", concurrentDownloads=None):
    self.executor = ThreadPoolExecutor(max_workers=concurrentDownloads)
    self.youtubeLock = TimedLock(settings["youtubeWait"])
    log.info("Initialized Download and Conversion Processor")
    
  @staticmethod
  def flattenDict(inputDict: dict) -> list:
    """ Flattens a dictionary into a list where values follow keys. Used for making command line arguments """
    return sum([[key] if type(value) is bool else [key, value] for key, value in inputDict.items() if value], list())

  def submitSong(self, songID, progressFunction):
    log.debug("Submitting song '{}' for processing".format(songID))
    return self.executor.submit(self.processSong, songID, progressFunction)

  def processSong(self, songID, progressFunction):
    """ Downloads the info while downloading the video itself"""
    self.downloadSong(songID, progressFunction)

  def downloadSong(self, song, outputFunction=None, writeJSON=True):
    """
    Function to download a song, whether it exists or not already.
    :param song: A url for the song. Youtube-dl on the url should be a song, not a playlist.
    :param outputFunction: If given, should be a callable given two parameters: Current percentage (float) and download (float str followed by MiB/s or KiB/s). Will be called during execution
    :return: (Return code, full string of stdout and stderr returned by youtube-dl)
    """

    """
      -x: Extract audio
      --audio-format: sets the audio format from ogg to mp3
      --audio-quality: 0 is best
      --write-info-json: Writes the DASH information for the downloaded video to the filename with .info.json appended
    """
    audioOptions = {"-x": True, "--audio-format": "mp3", "--audio-quality": "0"}
    if writeJSON:
      audioOptions["--write-info-json"] = True
    audioOptions.update(settings["youtubeSettings"])

    self.youtubeLock.acquire() # Wait the requisite amount of time
    log.debug("Downloading Song '{}'".format(song))
    obj = subprocess.Popen(
      [settings["youtube_dl"]] + # Executable
      self.flattenDict(audioOptions) + #Turn the dict items into a list where key is before value. Bools are special. If false, not added, otherwise only key
      ["-o", os.path.join(self.folder, settings["formatString"])] + #Output format and folder
      ["--", song], #Then add song as input
      **settings["pipeOptions"], #Add in subprocess options
      stdout=subprocess.PIPE #Also this for now
    )
    
    outputText = ""
    for line in obj.stdout:
      outputText += line
      #print(line.rstrip())
      match = re.match(r"\[download\]\s+([\d.]+)% of \S+ at\s+([\d.]+\S+)", line) #Matches the download update lines
      if match:
        percent, downloadRate = match.group(1, 2)
        if callable(outputFunction):
          outputFunction(float(percent), downloadRate) #Update this if we have items
    return obj.wait(), outputText # Wait for process to complete and get return code. Also return the whole output printed to stdout
    
  def getInfo(self, url, flat=True):
    """
    Gets info for a playlist or a song
    :param url: Either youtube id or url
    :param flat: If true, uses --flat-playlist, otherwise downloads full info
    :return: If errored, returns string output from process. Otherwise, returns dict returned by youtube-dl
    """
    try:
      self.youtubeLock.acquire() # Wait the requisite amount of time
      log.debug("Getting info for '{}'".format(url))
      #                                                                                                                                         -- in case youtube url begins with "-"
      output = subprocess.check_output([settings["youtube_dl"], "-J", "--flat-playlist" if flat else ""] + self.flattenDict(settings["youtubeSettings"]) + ["--", url], **settings["pipeOptions"])
    except subprocess.CalledProcessError as e:
      return e.output
    else:
      return json.loads(output)

  def saveInfo(self, id:str, toSetDict:dict=None):
    if toSetDict is None: # If we aren't given anything, get the info from youtube
      toSetDict = self.getInfo(id)

  def changeMP3Tags(self, filePath, optionsDict):
    file = EasyID3(filePath)
    for key, value in optionsDict.items():
      file[key] = value
    file.save(v2_version=3) # Save as version 3 so windows can see the tags

handler = VideoProcessor()
if __name__ == "__main__":
  
  info = handler.getInfo(r"https://www.youtube.com/playlist?list=PLeihsqiyYb0E_Ny6jBSvNdqYwKDQGEns1")
  info = handler.getInfo(r"https://www.youtube.com/playlist?list=PLeihsqiyYb0EQjDvZY401UCdoxxOsDu24")
  print(info)
  if isinstance(info, str):
    print(info)
    raise AssertionError()

  entries = info["entries"]

  for song, func in [(entry["url"], lambda x, y, val=i: print(val, "--", x, y)) for i, entry in enumerate(entries)]:
    handler.submitSong(song, func)

  """
  for i, entry in enumerate(entries):
    url = entry["url"]
    songFile = os.path.join(GlobalOptions["videoStorageDir"], url+".mp3")
    print("Song {:2}/{:2}: {}".format(i+1, len(entries), url))
    code, output = handler.downloadSong(url, lambda x, y: print("-----", x, y))
    if code:
      print("ERROR:", output)
      continue
    handler.changeMP3Tags(songFile, {"organization": entry["title"]})
  """