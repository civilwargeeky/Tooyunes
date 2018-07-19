#This module implements our own logging
import logging, logging.handlers, queue, sys

#Should be included by the display to poll
consoleQueue = queue.Queue(100)
EmptyException = queue.Empty  #For convenience in handlers

factory = logging.getLogRecordFactory()


def print_formatting(*args, **kwargs):
  newArgs = list(args)
  #So this changes the message attribute to be a string of the msg and all args joined together
  newArgs[4] = " ".join([str(i) for i in ([args[4]] + list(args[5]))])
  newArgs[5] = tuple()  #Then don't try formatting again
  return factory(*newArgs, **kwargs)


logging.setLogRecordFactory(print_formatting)


class NoErrorQueueHandler(logging.handlers.QueueHandler):
  def enqueue(self, record):
    try:
      super().enqueue(record)
    except queue.Full:  #Ignore records over max
      pass

#All the loggers
log = logging.getLogger("main")
log.setLevel(logging.DEBUG)
fileHandler = logging.FileHandler("last.log", mode="w", delay=True)
fileHandler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s"))
log.addHandler(fileHandler)
#Standard debug stream
outHandler = logging.StreamHandler(sys.stdout)
outHandler.setFormatter(logging.Formatter("[%(levelname)s]: %(message)s"))
log.addHandler(outHandler)
#Also add a handler for error handlers, py2exe makes a special file for this and will pop up an error box when program closes
errHandler = logging.StreamHandler(sys.stderr)
errHandler.setLevel(logging.ERROR)
errHandler.setFormatter(logging.Formatter("%(asctime)s ERROR!!! Please contact the program creator with this information: %(message)s"))
log.addHandler(errHandler)
#Add a logger to the GUI console
consoleHandler = NoErrorQueueHandler(consoleQueue)
consoleHandler.setLevel(logging.INFO)
consoleHandler.setFormatter(logging.Formatter("%(message)s"))
log.addHandler(consoleHandler)
