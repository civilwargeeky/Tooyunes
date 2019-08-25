# This defines the structure and functionality for the levels of music management
import json, logging, os, re, threading
import Settings
import FileHandler
import DatabaseHandler
import DownloadHandler

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
    
    self.songsExpected = []
    
    self.sources = {} # Dict of playlist id to playlist objects that we draw songs from
    
    self.changeSetLock = threading.Lock() # Mutex so we don't try to concurrently modify files
    self.changeSet = [] # A list of two-tuples, [0] is either file location of song or None [1] is 3-tuple of song id, playlist id, desired settings
    self.downloadSet = [] # List of ids that need to be downloaded
    
    self.rules = [] # List of rules that apply to this music set.
    
    self.ignored = [] # List of ids that we ignore from downloading. If already downloaded, won't be modified.
    
  def initialize(self, fileDict):
    """ 
    Function to initialize the music set from a dict in a file
    
    The file should contain a dict with the following:
      "name": Name of music set, also used as the file name
      "sources": list of playlist objects - a dict of "id", "title", "folder"
      "songs": list of song objects - a dict of see Song "initialize" for obj
        
    """
    self.name = fileDict["name"]
    
    log.debug("Parsing MusicSet file")
    # Initialize all playlist objects
    for sourceDict in fileDict["sources"]:
      newPlaylist = Playlist(self, sourceDict)
      self.sources[newPlaylist.id] = newPlaylist
      
    # Initialize all songs from file information
    for song in fileDict["songs"]:
      songObj = Song(self, song)
      # If there is a playlist, we want to add in the settings from the playlist for each song
      if songObj.playlist in self.sources:
        songObj.setPlaylist(self.sources[songObj.playlist])
      self.songsExpected.append(songObj)
      
    log.debug("Gathering data from downloaded files")
    # Then get all information on files currently downloaded
    directory = os.path.join(Settings.application.outputDir, self.name)
    if not os.path.isabs(directory):
      directory = os.path.join(".", directory)
    if os.path.isdir(directory):
      songsActual = [] # TODO: Just do an update of this so actual matches expected after initialization
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
              if key == "playlist" and value:
                if value in self.sources:
                  newSong.setPlaylist(self.sources[playlist])
              else:
                if value is not None:
                  newSong.settings[key] = value
             
            songsActual.append(newSong)
          if baseDir != directory: # Assume tree only one deep, if not going through playlist folders, clear all other dirs.
            dirs.clear()
        
    else:
      log.warning("In MusicSet initializer, output directory doesn't exist!")
      
    
    
    log.info("Loaded information on \n  {} playlists\n  {} song information".format(len(self.sources), len(self.songsExpected)))
    
  def save(self):
    toSave = {"name": self.name, "sources": [], "songs": []}
    for source in self.sources.values():
      toSave["sources"].append({"id": source.id, "title": source.title, "folder": source.folder})
    for song in self.songsExpected:
      toSave["songs"].append(song.save())
    return toSave
    
  def saveToFile(self, filename):
    with open(filename, "w") as file:
      json.dump(self.save(), file)
    
  def runRules(self, song, addToChangeSet=False):
    """ Runs all rules, generates expected folder, filename, and mp3 id3 info. Should be run after initialization completed """
    originalSettings = song.settings.copy() # Creat a dumb dict of the settings
    songInfo = DatabaseHandler.getSong(song.id)
    for rule in self.rules:
      rule.run(song, songInfo)
    if song.playlist and song.playlist in self.sources:
      for rule in self.sources[song.playlist].rules:
        rule.run(song, songInfo)
        
    # After going through all rules, ensure we have a filename and make sure filename and folder are allowable
    if not song.settings["filename"]:
      raise RuntimeError("Song doesn't have a filename property")
    for key in ("filename", "folder"):
      song.settings[key] = re.sub(r'[/\:<>?*"|]', "", song.settings[key])
        
    if addToChangeSet:
      newSettings = song.settings.copy()
      if newSettings != originalSettings: # I don't want to rewrite __equals__, so we'll just copy again
        origPath = os.path.join(originalSettings["folder"], originalSettings["filename"])
        self.changeSet.append((origPath, song)) # Add a tuple of settings as they are now
    
  def runRulesAllSongs(self):
    for song in self.songsExpected:
      runRules(song, addToChangeSet=True)
      
  def makeSong(self, id, playlist=None):
    """ 
      Creates a new song object, using data from database.
      :param id: ID of song as gotten from youtube
      :param playlist: id of the playlist this song came from (or None)
      
      When complete, the song will be added to list of complete and an entry in changeSet will be made
    """
    songInfo = DatabaseHandler.getSong(id)
    song = Song(self)
    song.id = id
    if playlist and playlist in self.sources:
      song.setPlaylist(self.sources[playlist])
    self.runRules(song)
    self.songsExpected.append(song)
    return song
    
  def resolveChangeSet(self):
    """ Function to apply all the changes in the changeSet. Expects all necessary songs have been downloaded already """
    with self.changeSetLock:
      for firstObj, song in self.changeSet:
        if firstObj is None: # If the file doesn't exist in it's proper destination
          FileHandler.copySong(song.id, song.settings["folder"], song.settings["filename"],
            title=song.settings["title"],
            artist=song.settings["artist"],
            album=song.settings["album"],
            organization=(song.playlist or "")+"/"+song.id
          )
          self.songsExpected.append(song) # Add to the list of songs we expect to have
        else: # If the file already exists
          dest = os.path.join(song.settings["folder"], song.settings["filename"])
          if dest != firstObj:
            FileHandler.moveSong(firstObj, dest)
          FileHandler.changeTags(dest, {
            "title": song.settings["title"],
            "artist": song.settings["artist"],
            "album": song.settings["album"],
            "organization": (song.playlist or "")+"/"+song.id
          })
      self.changeSet.clear()
  
  def getDownloadCallback(self, id, playlist=None):
    """ Makes a new callback function to be used as the "complete function" for downloader
    Any other function that downloads for this set should include this callback for the file being downloaded """
    
    def callback(songID, success):
      if success:
        with self.changeSetLock:
          self.changeSet.append((None, self.makeSong(id, playlist)))
        self.resolveChangeSet()
      else:
        log.error("Song failed to download: "+songID)

    return callback
    
  def songExists(self, songID, playlistID):
    for songObj in self.songsExpected:
      if songObj.id == songID and songObj.playlist == playlistID:
        return songObj
    return False

  def getDownloadSet(self):
    # NOTE: THIS HAS THE SIDE EFFECT OF MOVING ALL SONGS THAT ARE DOWNLOADED BUT NOT IN EXPECTED SET
    songsHash = {}
    for song in self.songsExpected:
      songsHash[song.getOrganization()] = True
    toDownload = []

    for source in self.sources:
      songsInPlaylist = DatabaseHandler.addSongFromDict(DownloadHandler.handler.getInfo(source, playlist=True))
      for songID in songsInPlaylist:
        if songID not in self.ignored:
          if DatabaseHandler.isDownloaded(songID):
            if not self.songExists(songID, source):
              self.changeSet.append((None, self.makeSong(songID, source)))
          else:
            toDownload.append((songID, source))
      if self.changeSet:
        self.resolveChangeSet()

    return toDownload


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
    self.rules = []

    if init: self.initialize(init) # Removes an extra line if we are initializing and setting

  def initialize(self, loadDict):
    self.id = loadDict["id"]
    self.title = loadDict["title"]
    self.setFolder(loadDict["folder"])
    
  def setFolder(self, folder):
    self.folder = folder
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
    self.id = None # ID of this song
    self.playlist = None # ID of the playlist this song is associated with
    
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
    
  def save(self):
    """ Returns a dict of information to save """
    return {
      "id": self.id,
      "playlist": self.playlist,
      "settings": self.settings.getOverrides(), # We only want to save the things that are overrides, not things determined from rules
    }
  
  def getOrganization(self):
    """ We store information used to find the song again in the "organization" tag of the mp3, so this is the song's unique identifier"""
    return (self.playlist or "") + "/" + self.id
  
  def setPlaylist(self, playlist): # Expects playlist object, not id
    self.playlist = playlist.id
    self.setDefaultDict(playlist.settings)
    
  def setDefaultDict(self, defaultDict):
    self.defaults.setDefaultDict(defaultDict)

def RuleRegister(name): #Helper method to add registration so we can load rules from file
  def inner(otherClass):
    Rule._rulesTypes[name] = otherClass
    otherClass._name = name
    return otherClass
  return inner

class Rule:
  """
  A "Rule" is a coupling of trigger to output that acts on a Song object, taking information from the song database if necessary
    The rule will modify the defaults of a song (which is the defaultDict of the settings object) so that overrides are not overridden
  """
  _rulesTypes = {} # Dict of rule name to rule

  @classmethod
  def getRule(name):
    return _rulesTypes[name]

  def __init__(self):
    self._name = None
    self._info = {} # A json-serializable object with settings for the rule

  def getName(self):
    return self._name

  def function(self, songInfo):
    """ This should be provided in extended classes, takes in songInfo and returns a dict of updates """
    raise NotImplementedError()
    
  def save(self):
    """ Returns a dict of info needed to reconstruct this rule object """
    return self._info
    
  def run(self, song, songInfo=None):
    """
    Runs the rule on the selected song.
    :param song: A song object, it's defaults will be modified by this function
    :param songInfo: The song's information from the database. If not given, will be obtained in this function
    :returns: True if any the function returned any updates, false otherwise
    """
    
    if songInfo is None:
      songInfo = DatabaseHandler.getSong(song.id) # May raise KeyError if song doesn't exist
    
    songUpdates = self.function(songInfo)
    if songUpdates:
      song.defaults.update(songUpdates)
      return True
    return False

@RuleRegister("ArtistTitle")
class ArtistTitleRule(Rule):
  def __init__(self, useYoutubeMetadata):
    super().__init__()
    self._info["meta"] = useYoutubeMetadata

  def function(self, info):
    meta = self._info["meta"]
  
    artist = (info["songArtist"] if meta else None) or re.match("(.+?) ?[|-]", info["title"])
    try: artist = artist.group(1)
    except AttributeError: pass
    # Note: Artist could still be "None" here
    
    title = (info["songTitle"] if meta else None) or re.search("[|-] ?(.+)", info["title"])
    try: title = title.group(1)
    except AttributeError: pass
    
    if not artist or not title:
      title = info["title"]

    # Get rid of "lyrics", "official lyrics", "official video", "music video", "official music video", "with lyrics", etc. possibly in parenthesis
    title = re.sub(r" ?\(?(?:official |with )?(?:music )?(?:lyrics|video|audio|lyric video)\)?", "", title, flags=re.IGNORECASE)
    title = title.replace('"',"") # Remove quotes
    
    toRet = {}
    if meta:
      toRet["album"] = info["songAlbum"]
    toRet["title"] = title
    if not artist:
      toRet.update({"filename": title})
    else:
      toRet.update({"filename": "{} - {}".format(artist, title), "artist": artist})
    return toRet