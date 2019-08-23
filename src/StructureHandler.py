# This defines the structure and functionality for the levels of music management
import logging, os
import Settings
import FileHandler

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

class MusicSet:
  """
  A "MusicSet" is the overarching structure defined by a configuration file.
  It can have multiple playlists and sources, and most settings are defined at a music set level
  The MusicSet will maintain lists of the songs it contains
  """
  
  def __init__(self): 
    self.songSettings = songSettings.createInstance() # Create a new instance for default settings in this musicset
    
    self.name = None
    
    self.songsActual = []
    self.songsExpected = []
    
    self.sources = {} # Dict of playlist id to playlist objects that we draw songs from
    
    self.ignored = [] # List of ids that we ignore from downloading. If already downloaded, won't be modified.
    
  def initialize(self, fileDict):
    """ 
    Function to initialize the music set from a dict in a file
    
    The file should contain a dict with the following:
      "name": Name of music set, also used as the file name
      "sources": list of playlist objects - a dict of "id", "title", "folder"
      "songInfo": list of song objects - a dict of see Song "initialize" for obj
        
    """
    self.name = fileDict["name"]
    
    log.debug("Parsing MusicSet file")
    # Initialize all playlist objects
    for sourceDict in fileDict["sources"]:
      newPlaylist = Playlist(self, sourceDict)
      self.sources[newPlaylist.id] = newPlaylist
      
    # Initialize all songs from file information
    for song in fileDict["songInfo"]:
      songObj = Song(self, song)
      # If there is a playlist, we want to add in the settings from the playlist for each song
      if songObj.playlist in self.sources:
        songObj.setDefaultDict(self.sources.playlist.settings)
      self.songsExpected.append(songObj)
      
    log.debug("Gathering data from downloaded files")
    # Then get all information on files currently downloaded
    directory = os.path.join(Settings.application.outputDir, self.name)
    if not os.path.isabs(directory):
      directory = os.path.join(".", directory)
    if os.path.isdir(directory):
      for baseDir, dirs, files in os.walk(directory):
        for file in files:
          if os.path.splitext(file)[1] == Settings.application["musicExtension"]:
            newSong = Song(self)
            newSong.settings["filename"] = file
            if baseDir != directory: # If we aren't in the base directory
              newSong.settings["folder"] = os.path.basename(baseDir) # Assume only one folder deep, get the last element of this
            metadata = FileHandler.getTagData(os.path.join(baseDir, file))
            
            for key, value in metadata.items():
              if key == "id" and value:
                newSong.id = value
              else:
                if value is not None:
                  newSong.settings[key] = value
             
            self.songsActual.append(newSong)
          if baseDir != directory: # Assume tree only one deep, if not going through playlist folders, clear all other dirs.
            dirs.clear()
        
    else:
      log.warning("In MusicSet initializer, output directory doesn't exist!")
    
    log.info("Loaded information on \n  {} playlists\n  {} song information\n  {} actual song files".format(len(self.sources), len(self.songsExpected), len(self.songsActual)))
    
  def sync(self):
    event = donwloadSongsWeDontHave(currentConfig)
    
    renameSongsWeDoHave(self.generateConfig())
    
    event.wait()

class Playlist:
  """
  The playlist is only valid for expected songs, you cannot associate existing songs to the playlist
  A playlist simply stores the playlist id, and default settings like folders
  """
  
  def __init__(self, musicSetParent, init=None):
    self.musicSet = musicSetParent
    self.settings = musicSetParent.songSettings.createInstance() # Playlist is another layer of settings from musicset
    self.id = None
    self.title = None
    self.folder = None
    
    if init: self.initialize(init) # Removes an extra line if we are initializing and setting
    
  def initialize(self, loadDict):
    self.id = loadDict["id"]
    self.title = loadDict["title"]
    self.setFolder = loadDict["folder"]
    
  def setFolder(self, folder):
    self.settings["folder"] = folder

# Settings that are made per-song, and which the defaults can be modified at the music-set level
songSettings = Settings.SettingsDict({
  "folder": "",
  "filename": None,
  ### These are items stored as MP3 data ###
  "title": "Default Song",
  "artist": "DJ Dan",
  "album": None,
})

class Song:
  """
  A song contains information regarding how a song should be stored, including artist overrides
  """
  
  def __init__(self, musicSet, init=None):
    """
    musicSet: A MusicSet instance where this song gets its song settings from.
    """
    self.id = None
    self.playlist = None
    
    # So each song should have a default value which is assigned automatically, then allow for an override from the user as settings
    self.defaults = musicSet.songSettings.createInstance()
    self.settings = self.defaults.createInstance()
    
    if init: self.initialize(init)
    
  def initialize(self, fileDict):
    """
    Setup a song from a dict as should be obtained from file
    
    "id": Video id
    "playlist": Either None for unknown/one-off songs, or a playlist id
    "settings": This is the overrides, not the defaults. Defaults should be generated from rules on load
    """
    self.id = fileDict["id"]
    self.playlist = fileDict["playlist"]
    self.settings.update(fileDict["settings"])
  
  def setDefaultDict(self, defaultDict):
    self.settings.setDefaultDict(defaultDict)
  
  