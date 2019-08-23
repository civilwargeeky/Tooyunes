# # # Placeholder for settings module. Basically will include getters and setters. Structure decided later.
# Maybe like syntactic override for having a dict to . notification. So could do like
# Settings.log["test"] or Settings.log.test

class NoDefaultWarning(Warning):
  pass

class SettingsDict(dict):
  """
  Each setting will be 2-layered, with a real value, and then a set of defaults backing it in 2 separate dicts
  Because you can create "instances" of settings which use the settings as defaults, you can create tiered settings,
    where changes to parents are propogated down the line to lower levels.
  """
  
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._defaults = {}
  
  def __getattr__(self, name):
    try:
      return self[name]
    except KeyError:
      raise AttributeError from None
      
  def __setattr__(self, name, value):
    if name != "_defaults" and name in self:
      self[name] = value
    else:
      super().__setattr__(name, value)
      
  def __len__(self):
    """ Size of dict is sum of all elements in dict and defaults """
    return len(set(self) | set(self._defaults))
    
  def __missing__(self, key):
    """ If key wasn't in main dict, return the default """
    return self._defaults[key]
    
  def __iter__(self):
    return iter(set(super().__iter__()) | set(self._defaults))
    
  def __str__(self):
    temp = dict(self._defaults)
    for item in self: # Can't figure out what mechanism "update" uses, so this will do
      temp[item] = self[item]
    return str(temp)

  def __repr__(self):
    temp = dict(self._defaults)
    for item in self: # Can't figure out what mechanism "update" uses, so this will do
      temp[item] = self[item]
    return repr(temp)
    
  def __contains__(self, key):
    """ Returns true if in defaults or overlay dict
      NOTE: setattr depends on this, and will set a value in the main dict if a default exists
            This results in slightly different behaviour if using .notation or [notation] as [notation] will allow settings items without a default
    """
    return super().__contains__(key) or key in self._defaults
      
  def createInstance(self, setDefaults = True):
    """
    Has two modes:
      setDefaults = False: New object has a shallow copy of settings, and shared defaults
      setDefaults = True: New object has cleared settings, and the defaults are shared with the settings of the parent
        This is for config-defined defaults, so that the global "parent" holds the defaults as settings, and passes them onto children
    """
    if setDefaults:
      toRet = self.__class__() # Blank constructor
      toRet._defaults = self # Then for the defaults we could have another layer (or two!) to get a value
    else:
      toRet = self.__class__(self) # Should be a copy constructor
      toRet._defaults = self._defaults
    return toRet
    
  def setDefaultDict(self, defaultDict):
    if not issubclass(defaultDict, dict):
      raise TypeError("SettingsDict default dict must be dict subclass")
    for key in self.keys():
      if key not in defaultDict:
        raise KeyError("SettingsDict default dict must contain all keys in current dict, does not contain '{}'".format(key))
    # Actually set dict
    self._defaults = defaultDict
  
  def updateDefaults(self, updateDict = None, **updates):
    """ Will update defaults from either an update dictionary or a set of keyword argument updates """
    if updateDict is None: # If not specified as dict, use kwargs. If these are empty, do nothing
      updateDict = updates
    self._defaults.update(updateDict)
    
  def getDefault(self, key):
    return self._defaults[key]
    
  def isDefault(key):
    """ Returns true if the key is in the defaults and not in the top layer, false otherwise """
    return not super.__contains__(key) and key in self._defaults
    
  # NOTE: Keys should always be cleared rather than set to the default value, as the default is global and could be changed.
  def resetKey(self, key):
    del self[key]
    
  def resetAll(self):
    self.clear()

# Here is globally-accessible objects. These can be updated between modules
youtubeSettings  = SettingsDict()
ui               = SettingsDict()
databaseSettings = SettingsDict()
application      = SettingsDict()

application.updateDefaults({
  "outputDir": "", # By default just put it in the working directory
  "musicExtension": ".mp3",
})
