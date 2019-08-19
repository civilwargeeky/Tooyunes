# This defines the structure and functionality for the levels of music management

import Settings

class MusicSet:
  """ 
  A "MusicSet" is the overarching structure defined by a configuration file.
  It can have multiple playlists and sources, and most settings are defined at a music set level
  """
  
  def __init__(self): 
    self.name = None
    self.settings = Settings.musicSet.createInstance()