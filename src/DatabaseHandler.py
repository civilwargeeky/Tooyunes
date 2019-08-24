import json, logging, os, os.path
from time import time
import Settings

settings = Settings.databaseSettings
settings.updateDefaults({
  "videoStorageDir": "_VideoStore",
  "databaseFile": "_data.json", # This is a big json file that contains all the information for all songs downloaded
})

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

def getVideoFolder(id=None):
  if id is not None:
    return os.path.join(settings["videoStorageDir"], id+Settings.application["musicExtension"])
  return settings["videoStorageDir"]

"""
Format of Database:
  "videos": Dict of video id (in youtube) to information about that song
    [song id]: {
      title: title of the video
      author: name of the channel this video came from
      length: length of song (in seconds)
      downloadedAt: timestamp of when the song was downloaded. None or 0 for not downloaded currently
      songTitle: alt_title, if available
      songArtist: artist, if available
      songAlbum: album, if available
      ytinfo: all the data given about this song in the playlist abstract
    }
"""
database = {}

def initialize(clear=False):
  database.clear()
  
  log.debug("Initializing song database")
  song_files = []
  try: 
    os.makedirs(getVideoFolder())
    log.debug("Created song cache folder")
  except FileExistsError: 
    song_files = os.listdir(getVideoFolder())
    log.debug("Song cache folder already exists, contains {} songs.".format(len(song_files)))

  if clear:
    log.info("Clearing Database")
  else:
    try:
      with open(settings["databaseFile"]) as file:
        database.update(json.load(file))
      log.debug("Database file found and loaded")
    except FileNotFoundError: # If there's no file yet, just ignore this
      log.debug("Database file not found, storing in RAM")
    
  if "videos" not in database:
    database["videos"] = {}
    
  # Here we rectify any videos that exist in the database but not the files or vice-versa
  for song_id in list(database["videos"]): # List so we can delete
    if song_id+Settings.application["musicExtension"] not in song_files: # If the song's id doesn't correspond with a file
      if not "title" in getSong(song_id): # If it is just a dummy from a previous iteration, don't include it
        del database["videos"][song_id]
      else:
        getSong(song_id)["downloadedAt"] = None # Mark that video isn't downloaded
      
  # Vice-Versa
  for song_file in song_files:
    song_id, song_ext = os.path.splitext(song_file)
    if song_ext not in Settings.application["musicExtension"]: # If there were any extraneous file left over, remove them at this time
      log.debug("found extranneous file '{}', removing".format(song_file))
      os.remove(os.path.join(getVideoFolder(), song_file))
    elif song_id not in database["videos"]: # If the file doens't correspond to a database entry
      log.debug("Song '{}' has file but not in database, adding dummy entry".format(song_id)) # NOTE: This could probably be done asynchronously so to not hang up load
      getSong(song_id)["downloadedAt"] = int(time()) # Creates a blank song if it doesn't exist
     
  save() # Now that all songs have been rectified
  log.info("Database module initialized")

def getSong(id):
  try:
    return database["videos"][id]
  except KeyError:
    toRet = {"downloadedAt": None}
    database["videos"][id] = toRet
    return toRet
    
def isDownloaded(id):
  try:
    return bool(database["videos"][id]["downloadedAt"])
  except KeyError:
    return False

def addSongFromDict(inDict):
  """
  This takes in a dictionary and updates our database from it. Dict should be from a song, flat-playlist, or a playlist entry
  """
  # If playlist, add all songs from inside
  if "_type" in inDict:
    if inDict["_type"] == "playlist":
      for entry in inDict["entries"]:
        addSongFromDict(entry)
      return
    if inDict["_type"] == "url":
      log.debug("Adding playlist song: "+inDict["title"])
      getSong(inDict["id"])["title"] = inDict["title"]
  else: # Otherwise assume its a full song dict
    songDict = getSong(inDict["id"])
    for myKey, theirKey in (
      ("title", "title"),
      ("author", "uploader"),
      ("length", "duration"),
      ("songTitle", "alt_title"),
      ("songArtist", "artist"),
      ("songAlbum", "album")
    ):
      songDict[myKey] = inDict[theirKey]
    for key in ("formats", "requested_formats"): # These are like horrendously long, and time-dependant so don't save it
      if key in inDict:
        del inDict[key]
    #songDict["ytinfo"] = inDict # Sure it's a bit of redundant information, but it may be useful!
  
def setDownloaded(id, state=True):
  """ Sets a video as downloaded or deleted """
  getSong(id)["downloadedAt"] = int(time()) if state else None

def save():
  log.debug("Saving database")
  with open(settings["databaseFile"], "w") as file:
    json.dump(database, file)
  
def printSongs():
  def clamp(string, size):
    if len(string) > size:
      string = string[:size-2] + ".."
    return string.ljust(size)

  copy = database["videos"].copy()
  for key in list(copy):
    if "title" not in copy[key]:
      del copy[key]
  keys = ("title", "songTitle", "songArtist", "songAlbum")
  print("-"*80, end="")
  print("|".join(clamp(i, 19) for i in keys))
  print(("-"*19+"+")*3+"-"*20, end="")
  for key, value in sorted(copy.items(), key=lambda tup: tup[1]["title"]):
    print("|".join(clamp(value[i] or "", 19) for i in keys))
  
initialize()
