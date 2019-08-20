# This defines the structure and functionality for the levels of music management

"""
Class Structure
  MusicSet: The music

"""

import Settings

# For settings related to all musicsets, and should be edited in other modules
Settings.musicSet.updateDefaults({
  "name": "Default Set",
  "playlists": None, # Should be a dict of url to folder name. Multiple urls can go to the same folder, if desired.
    # NOTE: Could have a situation where multiple playlists in same folder have same id. This should be okay we do settings per-id globally
  "ignored": [], # List of video ids that are ignored from download
})

# Settings that are made per-song, and which the defaults can be modified at the music-set level
songSettings = Settings.SettingsDict({
  "id": None, # Youtube/Song id of song
  "folder": "",
  ### These are items stored as MP3 data ###
  "title": "Default Song",
  "artist": "DJ Dan",
  "album": None,
})


class MusicSet:
  """
  A "MusicSet" is the overarching structure defined by a configuration file.
  It can have multiple playlists and sources, and most settings are defined at a music set level
  The MusicSet will maintain lists of the songs it contains
  """
  
  def __init__(self): 
    self.settings = Settings.musicSet.createInstance()
    self.songSettings = songSettings.createInstance() # Create a new instance for default settings in this musicset
    

class Song:
  """
  A song contains information regarding how a song should be stored, including artist overrides
  """
  
  def __init__(self, parent):
    """
    parent: A MusicSet instance where this song gets its song settings from.
    """
    self.settings = parent.songSettings.createInstance()