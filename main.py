import tkinter as tk
from urllib.request import urlopen #For update checking



def main():
  #First thing we do is check for updates
  response = urlopen()

  root = tk.Tk()
  root.title("Title")
  root.mainloop()