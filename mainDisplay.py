#Handles all the GUI work for the main program
import math
import tkinter as tk
from tkinter import ttk
from log import log, consoleQueue, EmptyException
from os.path import join
from PIL import Image, ImageTk


class Window(tk.Tk):
  def __init__(self, title = None, icon = join("img", "mainIcon.ico"), *args, **kwargs):
    super().__init__(*args, **kwargs)
    if title: self.title(title)
    if icon: #Only add it if we can't, don't error
      try: self.iconbitmap(icon)
      except: pass
    #ttk.Style().theme_use("clam") #Looks weird when widgets don't take up whole space. Maybe someday

class MenuBar(tk.Menu):
  def __init__(self, parent, toAdd = None, tearoff=0):
    print("Making new bar")
    super().__init__(parent, tearoff=tearoff)
    if toAdd:
      self.addOptions(*toAdd)
  
  #Adds options to a menubar
  #PRE: each arg should be a tuple of the form (label, [options dict,] command/subtree tuple)
  #  where label is a string label, the options dict, if specified, should contain options for the underlying add command
  #  if "type" option is specified, it should contain "command", "checkbutton", or "radiobutton"
  #  "cascade" should not be given as a type, cascades should be specified by having a tuple
  #  for their last option. Separators are defined by having a label of "-". (Or with type "separator" if wanted)
  #  The last option should be either None, a callable function, or a tuple/list describing submenus
  #NOTE: Option lists are best kept as lists, because tuples with 1 element are annoying and sneaky, masquerading as just parenthesis
  def addOptions(self, *args):
    for element in args: #Each element is a tuple describing the list option
      print("Adding element:", element)
      if not isinstance(element, (tuple, list)):
        raise TypeError("MenuBar expected a list/tuple, got '"+str(type(element))+"'")
      if element[0] == "-": #Special case
        self.add_separator()
        continue
        
      toAdd   = "command" #By default
      options = {}
      label   = element[0]
      action = element[1] #Assuming we have no options
      if isinstance(element[1], dict): #If we have an options list
        print("We have an options list")
        try:
          toAdd = element[1]["type"]
          del element[1]["type"] #If it existed, remove it
        except KeyError:
          pass
        options = element[1]
        try:
          action = element[2] #If we keyerror here there was no action
        except IndexError: #Yeah, we still want an index error, just be a bit more descriptive
          raise IndexError("MenuBar expected a command following options dict")
      if isinstance(action, (tuple, list)): #We are adding a cascade
        print("Adding a cascade")
        print("Action: ", action)
        newMenu = MenuBar(self) #Then we recurse to the next one
        newMenu.addOptions(*action) #The base case being a dropdown with only commands, no dropdown
        self.add_cascade(label=label, menu=newMenu, **options)
      elif toAdd == "separator":
        self.add_separator(**options)
      else: #If we are just adding a command of some type
        print("Adding option")
        self.add(toAdd, label=label, command=action, **options)
      

# Background should be applied to a Frame. When the size of the frame is changed, the image size is updated
class Background():
  def __init__(self, parent, filename):
  
    self.parent = parent
    self.size = (0,0) #Set size to fake value
    self.filename = filename #Set initial filename
    self.img = None
    self.label = tk.Label(parent)
    self.label.place(x=0, y=0, relwidth=1, relheight=1)
    
    #We configure when the window opens, so we will get properly sized
    parent.bind("<Configure>", self.receiveConfigure)
    
  def updateImage(self, filename = None):
    if not self.img: #If this is the first time we load image
      self.img = Image.open(self.filename)
    elif filename and filename != self.filename:
      self.filename = filename
      self.img = Image.open(filename)
    #Find the smallest size so that the image doesn't overflow the
    multiplier = max(*[self.size[i]/self.img.size[i] for i in range(2)])
    # log.info(self.img.size)
    # log.info(self.size)
    # log.info(multiplier)
    try:
      newImg = self.img.resize([math.floor(i * multiplier) for i in self.img.size], Image.BICUBIC)
      #newImg = newImg.crop([0, 0, self.size[0], newImg.size[1]]) #Crop so it's left-aligned and vertically center
    except ValueError: #Done when the canvas size is listed as (1,1) before full initialization
      return #Don't do anything here
    self.tkImage = ImageTk.PhotoImage(newImg)
    self.label.config(image=self.tkImage)
  
  def receiveConfigure(self, event = None):
    newSize = (event.width, event.height)
    if self.size != newSize:
      self.size = newSize #Update our size
      self.updateImage()  #Change the background if size changed


class MultiColumnList(ttk.Treeview):
  def __init__(self, parent, columns):
    self.lastSorted = None
  
    super().__init__(parent, columns=columns, show="headings", height=0)
    #Makes a scrollbar. Scrolling on the bar moves the listview up or down
    scrollbar = ttk.Scrollbar(parent, command=self.yview)
    #Configures the tree such that scrolling while focused on the tree moves the bar
    self.configure(yscrollcommand=scrollbar.set)
    
    #Properly grid so they expand nicely
    self.grid(column=0, row=0, sticky="new")
    scrollbar.grid(column=1, row=0, sticky="ns")
    
    #Configure the columns so they expand properly
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(0, weight=1)
    
    #Add names for all the headings
    for column in columns:
      self.heading(column, text=column, anchor="w",
        command=lambda column=column: self.sortby(column, False))
        
      
  def addItem(self, values):
    self.insert('', 'end', values=values)
    self.configure(height=len(self.get_children("")))
    
  def sortby(self, column, descending=False):
    #Makes a list up tuples with (Value, child name) to be sorted
    data = [(self.set(child, column), child) for child in self.get_children("")]
    
    #Tuples are sorted element-by-element so first element is the column value
    data.sort(reverse=descending)
    
    for i, item in enumerate(data):
      #Moves the item name to a new index
      self.move(item[1], '', i)
    
    #Then reverse the direction the function will sort
    # https://www.compart.com/en/unicode/block/U+25A0
                                         #small down arrow            #small up arrow
    self.heading(column, text=column+" "+("\u25BF" if descending else "\u25B5"),
      command=lambda col=column: self.sortby(col, not descending))
    #Change last heading being sorted to not have an arrow (if is not this column)
    if self.lastSorted and self.lastSorted != column:
      self.heading(self.lastSorted, text=self.lastSorted)
    self.lastSorted = column
    
class TextQueueWatcher(tk.Text):
  def __init__(self, parent, queue, pollTime = 250, maxChars = 1000000):
    self.parent = parent
    self.queue  = queue
    self.pollTime = pollTime #In milliseconds
    self.maxChars = maxChars #Maximum chars before we start dropping lines
    self._hasInsert = False
    super().__init__(parent, width=15, height=1, state="disabled")
    #Whenever size changes, reset to end of list
    parent.bind("<Configure>", self.scrollToEnd)
    
    #Start waiting for queue messages
    self.poll()
    
  def insertMessage(self, msg):
    print(msg)
    print(dir(msg))
    self.insert(msg.msg)
    
  def insert(self, toInsert):
    #First line we don't have a newline
    if self._hasInsert: toInsert = "\n"+toInsert
    #Set state so we can write
    self.config(state="normal")
    #First check if we have too big of a thing
    if len(self.get("1.0", "end-1c")) > self.maxChars:
      #From: https://stackoverflow.com/q/26267069/2547742
      self.delete("1.0","2.0") #Just delete a line at a time. Eventually it should even out
    #Add to end
    super().insert("end", toInsert)
    #Remove ability to write
    self.config(state="disabled")
    #Scan to end
    self.scrollToEnd()
    #Set that we have inserted
    if not self._hasInsert: self._hasInsert = True
    
  #Only scrolls if it has focus
  def scrollToEnd(self, *arg):
    #If we aren't focused on this widget (user not scrolling)
    if self != self.focus_get(): 
      self.see("end")
      
  #Poll the queue for new messages to add
  def poll(self):
    while True:
      try:
        record = self.queue.get_nowait()
      except EmptyException: #Keep going until we have nothing to write
        break
      self.insert(record.msg) #Then insert message
      
    self.after(self.pollTime, self.poll)
    

def main(title, size = (200,400)):
  root = Window()
  root.title(title)
  root.minsize(width = size[0], height = size[1])
  
  menu = MenuBar(root, [
   ("File", []),
   ("Edit", []),
   ("Preferences", []),
  ])
  root.config(menu=menu)
  
  mainWindow = tk.Frame(root)
  console = tk.Frame(root)
  background = Background(mainWindow, "img/dark.png")
  
  a = MultiColumnList(mainWindow, ("Test", "Hi"))
  # a.addItem(("Column 1", "Column 2"))
  # a.addItem(("Column 4", "Column 1"))
  
  list = TextQueueWatcher(console, consoleQueue)
  list.pack(side="left", fill='both', expand=True)
  scrollbar = ttk.Scrollbar(console, command=list.yview)
  scrollbar.pack(side="right", fill="y", expand=False)
  #Configures the tree such that scrolling while focused on the tree moves the bar
  list.configure(yscrollcommand=scrollbar.set)
  # list.insert("Entry")
  
  root.grid_columnconfigure(0, weight=4)
  root.grid_columnconfigure(1, weight=1)
  root.grid_rowconfigure(0, weight=2)
  root.grid_rowconfigure(1, weight=1)
  mainWindow.grid(row=0, column=0, rowspan=2, sticky="nsew")
  tk.Frame(root, width=50).grid(row=0, column=1, sticky="nsew")
  console.grid(row=1, column=1, sticky="nsew")
  
  root.mainloop()

if __name__ == "__main__":
  main("Title")