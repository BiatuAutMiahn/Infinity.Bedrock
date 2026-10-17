Magic = "EzjJPGRZ05T7FK7Y"  # A 16 digit AlphaNumeric String
Alias = "bedrock_watch"              # Intended to be registered into globals(); TODO.
node=None                   # Global Place holders
logging=None                # ..

# Called before _loop_
def __init__(n,l):
    global node
    global logging
    node=n
    logging=l
    node.id=Magic
    logging.info("["+node.name+"]:\tInitialized")

# Called before node is reloaded after modification
def __reinit__(self):
  pass

# Called before node is terminated
def __deinit__(self):
  pass

# Called at intervals; default is 0.1s
def __loop__(self):
  pass
