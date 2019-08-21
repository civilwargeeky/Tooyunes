import logging, os, os.path
from Settings import databaseSettings as settings
import DownloadHandler

log = logging.getLogger()

settings.updateDefaults({
  "videoStorageDir": "_VideoStore",
  "datastore": "_data.json", # This is a big json file that contains all the information for all songs downloaded
  "musicExtension": ".mp3",
})

"""
Format of Database:
  "videos": Dict of video id (in youtube) to information about that song
    [song id]: {
      title: title of the video
      author: name of the channel this video came from
      length: length of song (in seconds)
      downloadedAt: timestamp of when the song was downloaded. None or 0 for not downloaded currently
      ytinfo: all the data given about this song in the playlist abstract
    }
"""
database = {}

def initialize():
  log.debug("Initializing song database")
  song_files = []
  try: 
    os.makedirs(settings["videoStorageDir"])
    log.debug("Created song cache folder")
  except FileExistsError: 
    song_files = os.listdir(settings["videoStorageDir"])
    log.debug("Song cache folder already exists, contains {} songs.".format(len(song_files)))

  try:
    with open(os.path.join(self.folder, settings["datastore"])) as file:
      database = json.load(file)
    log.debug("Database file found and loaded")
  except FileNotFoundError: # If there's no file yet, just ignore this
    log.debug("Database file not found, creating new")
    
  if "videos" not in database:
    database["videos"] = {}
    
  # Here we rectify any videos that exist in the database but not the files or vice-versa
  for song_id in database["videos"]:
    if song_id+settings["musicExtension"] not in song_files: # If the song's id doesn't correspond with a file
      database["videos"]["donwloadedAt"] = None # Mark that video isn't downloaded
      
  # Vice-Versa
  for song_file in song_files:
    song_id, song_ext = os.path.splitext(song_file)[0]
    if song_ext is not settings["musicExtension"]: # If there were any extraneous file left over, remove them at this time
      log.debug("found extranneous file '{}', removing".format(song_file))
      os.remove(os.path.join(settings["videoStorageDir"], song_file))
    elif song_id not in database["videos"]: # If the file doens't correspond to a database entry
      log.debug("Song '{}' has file but not in database, acquiring information".format(song_id)) # NOTE: This could probably be done asynchronously so to not hang up load
      song_info = DownloadHandler.handler.getInfo(song_id)
      if type(song_info) is dict: # If we successfully got the information, add to database
        addSong(song_info)
     
  save() # Now that all songs have been rectified
  log.info("Database module initialized")
      
def addSong(informationDict):
  pass
  
def save():
  pass