"""
    settings.py stores global variables for server program
"""
CLIENTS = {}  # associate socket info with client name
ROOMS = {}  # rooms with messages
OWNERS = {}  # dictionary correlates owner of room to room name
JOINED = {}  # correlates room name to users joined
SOCKETS_LIST = [] # list of used sockets

