import tkinter as tk

import updater
from log import log

#No matter what, we have to make sure TCL and TK can be found
from os import environ, getcwd, path
if path.exists("lib"):
  environ["TCL_LIBRARY"] = path.join(getcwd(), "lib", "tcl8.6")
  environ["TK_LIBRARY"]  = path.join(getcwd(), "lib", "tk8.6")


def main():
  updater.checkInstall()
  
  if updater.updateProgram(): #If this returns true, an update is in progress so we should exit
    return
  
  root = tk.Tk()
  root.title("Title")
  root.minsize(width=1000, height=1000)
  background_image = tk.PhotoImage(file="img\\bright.png")
  background_label = tk.Label(root, image = background_image)
  background_label.place(x=0, y=0, relwidth=1, relheight=1)

  root.mainloop()
  
  
if __name__ == "__main__":
  main()