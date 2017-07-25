import threading
import tkinter as tk
from tkinter import ttk
from os.path import join

from log import log

class Window(tk.Tk):
  def __init__(self, title = None, icon = join("img", "mainIcon.ico"), *args, **kwargs):
    super().__init__(*args, **kwargs)
    if title: self.title(title)
    if icon: #Only add it if we can't, don't error
      try: self.iconbitmap(icon)
      except: pass

def questionBox(message, title = "Message"):
  retVal = False
  def OK():
    nonlocal retVal
    retVal = True
    root.destroy()
  def Cancel():
    nonlocal retVal
    retVal = False
    root.destroy()

  try:
    root = Window(title = title)
    root.minsize(width = 200, height = 20)
    root.protocol("WM_DELETE_WINDOW", Cancel) #On pressing the X
    root.grid_columnconfigure(0, weight=1)
    frame = tk.Frame(root)
    frame.grid(row=0, column=0, sticky=tk.N)
    ttk.Label(frame, text = message, padding="15 15").grid(row=0, columnspan=2)
    ttk.Button(frame, text="OK", command=OK).grid(row=1, sticky=tk.E)
    ttk.Button(frame, text="Cancel", command=Cancel).grid(row=1, column=1, sticky=tk.W)
    
    root.mainloop()
    
    return retVal #If we exit nicely, we can give a return value
  finally: #No matter what, try to get rid of the window
    try: root.destroy()
    except: pass
    
def msgBox(message, title = "", size = None):
  root = Window(title = title)
  if size: root.minsize(width = size[0], height = size[1])
  tk.Label(root, text=message, padx=15, pady=15).pack(expand=True)
  root.mainloop()

#Makes a progressBar window
class FileDLProgressBar():
  def __init__(self, message, *args, title = "File Download"):
    self.started = False
    self.root = None #Prevent name error from not started
    self.title = title
    self.message = message
    self.args = []
    self.index = 0
    self.add(*args) #Add in any arguments if we want
    
  def getString(self):
    return self.message + "\n" + (self.args[self.index] or "")
    
  def start(self):
    if not self.started:
      self.started = True
      self.root = Window(title = self.title)
      self.root.protocol("WM_DELETE_WINDOW", self.close)
      self.label = tk.Label(self.root, text=self.getString())
      self.label.pack()
      self.progressBar = ttk.Progressbar(self.root, value=self.index)
      self.progressBar.pack()
      self.update()
    else: #If we've already started, just go to the next one
      self.next()
    
  def add(self, *args):
    self.args.extend(args)
    self.update()
    
  def addStart(self, *args):
    self.args = list(args) + self.args
    self.update()
    
  def update(self):
    if self.root:
      self.label["text"] = self.getString()
      self.progressBar["value"] = self.index
      length = len(self.args)-1
      self.progressBar.config(maximum=(length if length > 0 else 1))
      self.root.update()
    
  def next(self):
    self.index += 1
    if self.index < len(self.args):
      self.update()

  def close(self):
    if self.root:
      self.root.destroy()
      self.root = None #Signal that we can't update things anymore