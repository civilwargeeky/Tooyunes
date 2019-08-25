import logging, shutil, os, os.path
from mutagen.easyid3 import EasyID3, EasyID3KeyError

import DatabaseHandler

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

def copySong(id, folder, filename, title="", artist="", album="", organization=""):
  # Copy file to dest with file title and same extension
  src  = DatabaseHandler.getVideoFolder(id)
  dest = os.path.join(folder, filename+os.path.splitext(src)[1])
  os.makedirs(os.path.dirname(dest), exist_ok=True)
  shutil.copyfile(src, dest)
  
  # Then update tags as we can
  changeTags(dest, {
    "title": title,
    "artist": artist,
    "album": album,
    "organization": organization, # Seems like an innocuous place to put the id so we can retrieve it later
  })
  
  return dest
  
def moveSong(filepath, dest):
  os.makedirs(os.path.dirname(dest), exist_ok=True)
  return shutil.move(filepath, dest)
  
def changeTags(filename, tagsDict):
  """
  Will update all tags in the tagsDict. Tags must be of appropriate type. Most tags can be either string or list of strings
  """
  
  with open(filename, "rb+") as file:
    obj = EasyID3(file)
    for tag in tagsDict:
      try:
        obj[tag] = tagsDict[tag] if tagsDict[tag] is not None else ""
      except EasyID3KeyError:
        log.error("Could not set tag '{}' for file '{}'!".format(tag, filename))
    obj.save(file, v2_version=3) # Save it in a format recognizable by Windows
    
def getTagData(filename):
  """
  Returns a dict of title, artist, album, and id (organization)
  If a key doesn't exist, returns None for that one
  Doesn't catch FileNotFoundError s
  """
  toRet = {}
  with open(filename, "rb") as file:
    obj = EasyID3(file)
    for tag in ("title", "artist", "album", "organization"):
      try:
        toRet[tag] = obj[tag]
      except KeyError:
        toRet[tag] = None
    # So this should be id and playlist, but we store it in the "organization" tag
    toRet["playlist"], toRet["id"] = toRet["organization"].split("/")
    del toRet["organization"]
    
    return toRet