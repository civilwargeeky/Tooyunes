#Handles all the GUI work for the main program
import tkinter as tk
from tkinter import ttk
from os.path import join

class Window(tk.Tk):
  def __init__(self, title = None, icon = join("img", "mainIcon.ico"), *args, **kwargs):
    super().__init__(*args, **kwargs)
    if title: self.title(title)
    if icon: #Only add it if we can't, don't error
      try: self.iconbitmap(icon)
      except: pass
    #ttk.Style().theme_use("clam") #Looks weird when widgets don't take up whole space. Maybe someday

class MenuBar(tk.Menu):
  def __init__(self, parent, tearoff=0):
    print("Making new bar")
    super().__init__(parent, tearoff=tearoff)
  
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
      if (type(element) not in (tuple, list)):
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
      if type(action) in (tuple, list): #We are adding a cascade
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
      

from os.path import join
from tkinter import *
if __name__ == "__main__":
  import tkinter as tk
  from tkinter import ttk
  
  # root = tk.Tk()
  # var = tk.StringVar(root)
  # var.set("test")
  # ttk.OptionMenu(root, var, "test", "test", "other test", "thing").pack()
  
  # root.mainloop()
  
  # return
  
  root = tk.Tk()
  root.title("Title")
  root.minsize(width=1000, height=1000)
  
  def hello():
    print("hello!")

  a = MenuBar(root)
  a.addOptions(
    ("Test", [
      ("-",),
      ("Why", None),
      ("Test Button", {"type":"radiobutton"}, None),
      ("Test cascade", (
        ("Button Button", None),
        ("The best button", None),
        ("Second cascade!!!", [
          ["I am test button", (
            ("Hidden stuff", None),
          )]
        ])
      )),
      ("Test Button 2", {"type":"radiobutton"}, None)
    ])
  )
  root.config(menu=a)
  root.mainloop()  
  raise Exception
    
  menubar = Menu(root, tearoff=0)

  # create a pulldown menu, and add it to the menu bar
  filemenu = Menu(menubar)#, tearoff=0)
  filemenu.add_command(label="Open", command=hello)
  filemenu.add_command(label="Open", command=hello)
  filemenu.add_separator()
  filemenu.add_command(label="Exit", command=root.quit)
  menubar.add_cascade(label="File", menu=filemenu)

  # create more pulldown menus
  editmenu = Menu(filemenu, tearoff=0)
  editmenu.add_command(label="Cut", command=hello)
  editmenu.add_command(label="Copy", command=hello)
  editmenu.add_command(label="Paste", command=hello)
  filemenu.add_cascade(label="Edit", menu=editmenu)

  helpmenu = Menu(menubar, tearoff=0)
  helpmenu.add_command(label="About", command=hello)
  menubar.add_cascade(label="Help", menu=helpmenu)

  # display the menu
  root.config(menu=menubar)
  
  # background_image = tk.PhotoImage(file="img\\bright.png")
  # background_label = tk.Label(root, image = background_image)
  # background_label.place(x=0, y=0, relwidth=1, relheight=1)

  root.mainloop()