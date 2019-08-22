import json, io, subprocess, re, os, threading, logging
from concurrent.futures import ThreadPoolExecutor, wait as ThreadWait

# NOTE: FOR FUTURE https://github.com/ytdl-org/youtube-dl/#embedding-youtube-dl
# This module should only handle downloading the videos and putting them in the cache, updating the data store

import Settings
import DatabaseHandler

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

#This will be an object that handles inheritance, getting and setting in a sane way, etc.
settings = Settings.youtubeSettings
settings.updateDefaults({
  "concurrentDownloads": 8,
  "youtube_dl": r"resources\youtube-dl.exe",
  "pipeOptions": {"universal_newlines": True, "stderr": subprocess.STDOUT},
  "formatString": "%(id)s.%(ext)s",
  "youtubeWait": 1, # Time in between each call to youtube.com
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

  def __init__(self):
    self.executor = ThreadPoolExecutor(max_workers=settings["concurrentDownloads"])
    self.youtubeLock = TimedLock(settings["youtubeWait"])
    log.info("Initialized Download and Conversion Processor")
    
  @staticmethod
  def flattenDict(inputDict: dict) -> list:
    """ Flattens a dictionary into a list where values follow keys. Used for making command line arguments """
    return sum([[key] if type(value) is bool else [key, value] for key, value in inputDict.items() if value], list())
    
  def _testPlaylist(self, url):
    futures = []
    for info in self.getInfo(url)["entries"]:
      future = self.submitSong(info["id"], print, lambda id, success: print("Finished song {} with {}".format(id, "success!" if success else "failure")))
      future.id_ = info["id"]
      futures.append(future)
    try:
      print("Waiting for futures!")
      ThreadWait(futures)
    finally:
      DatabaseHandler.save()
      print("Failures:")
      for future in futures:
        if not future.result():
          print(future.id_)
    

  def submitSong(self, songID, *args, **kwargs):
    log.debug("Submitting song '{}' for processing".format(songID))
    return self.executor.submit(self.processSong, songID, *args, **kwargs)

  def processSong(self, songID, outputFunction=None, completeFunc=None):
    """
    Downloads the info while downloading the video itself
    :param songID: Should be the id of the song, not the youtube url
    :param completeFunc: Should be a function that takes two parameters: songID, and True/False for success
    """
    if "/" in songID:
      raise AssertionError("processSong cannot handle URLs, only youtube video ids")
    
    videoDir = DatabaseHandler.settings["videoStorageDir"]
    infoFile = os.path.join(videoDir, songID+".info.json")
    
    exit_code, text = self.downloadSong(songID, outputFolder = videoDir, outputFunction = outputFunction)
    if exit_code != 0: # If not successful, don't continue
      if callable(completeFunc):
        completeFunc(songID, False)
      return False
    
    with open(infoFile) as file:
      DatabaseHandler.addSongFromDict(json.load(file))
    os.remove(infoFile)
    
    DatabaseHandler.setDownloaded(songID)
    if callable(completeFunc):
      completeFunc(songID, True)
    return True

  def downloadSong(self, song, outputFolder="", outputFunction=None, writeJSON=True):
    """
    Function to download a song, whether it exists or not already.
    :param song: A url for the song. Youtube-dl on the url should be a song, not a playlist.
    :param outputFolder: A folder to put the video in. If not given, downloads to current directory
    :param outputFunction: If given, should be a callable given three parameters: song (str), Current percentage (float) and download (float str followed by MiB/s or KiB/s). Will be called during execution
    :param writeJSON: If true, will write JSON of request metadata to the video.info.json
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
      ["-o", os.path.join(outputFolder, settings["formatString"])] + #Output format and folder
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
          outputFunction(song, float(percent), downloadRate) #Update this if we have items
    return obj.wait(), outputText # Wait for process to complete and get return code. Also return the whole output printed to stdout
    
  def getInfo(self, url):
    """
    Gets info for a playlist or a song
    :param url: Either youtube id or url
    :return: If errored, returns string output from process. Otherwise, returns dict returned by youtube-dl
    """
    try:
      self.youtubeLock.acquire() # Wait the requisite amount of time
      log.debug("Getting info for '{}'".format(url))
      #                                                                                                                                         -- in case youtube url begins with "-"
      output = subprocess.check_output([settings["youtube_dl"], "-J", "--flat-playlist"] + self.flattenDict(settings["youtubeSettings"]) + ["--", url], **settings["pipeOptions"])
    except subprocess.CalledProcessError as e:
      return e.output
    else:
      return json.loads(output)

handler = VideoProcessor()



if __name__ == "__main__":
  handler._testPlaylist("https://www.youtube.com/watch?v=YBJhzfvdyKw&list=PLeihsqiyYb0EZSUolQ3QB6CR-TC-j37_p&index=4")