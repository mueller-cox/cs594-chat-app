import socket
import errno
import sys
import Client.messages as mm
import Base.settings as base
import Client.settings as c
import json

"""
    prompts user to enter choice of main actions: create room, join room, enter room, 
    list all rooms that can be entered, message multiple rooms, and quit
    Arguments: None
    Returns: char of user choice
"""


def intro():
    print("****Chat App Option Menu****")
    print("To List all available rooms enter $view_all$ ")
    print("To List the users belonging to a specific group enter $list$")
    print("To display this menu again enter $menu$")
    print("To Create Room enter $create$. ")
    print("To Join a Room(s) enter $join$. ")
    print("To Send a message enter $msg$")
    print("To leave a Room(s) $leave$")
    print("To Quit enter $quit$ ")
    print("My joined rooms:")
    for room in c.MY_ROOMS.keys():
        print(room)


"""
    list_all_rooms prints each room in the ALL ROOMS list to the console
    Arguments: None
    Returns: an int of the number of items printed
"""


def list_all_rooms():
    i = 0
    for room in c.ALL_ROOMS.keys():
        print(f"{room}")
        i += 1
    return i


"""
    list_room_members prints the list of users associated with room
    in ALL_ROOMS dictionary
    Arguments: None
    Returns: an int of the number of users printed
"""


def list_room_members():
    i = 0

    try:
        choice = input("List members in: ")
        if not choice:
            raise ValueError('empty string')
        if choice not in c.ALL_ROOMS.keys():
            raise ValueError('Room does not exist')
    except ValueError as e:
        print(e)
        return -1

    for user in c.ALL_ROOMS[choice]:
        print(f"{user}")
        i += 1
    return i


"""
    initialize_all_rooms copies contents of Server join table to ALL rooms sent as CONNECT message
    Argument: message in from server
    Return: nothing 
"""


def initialize_all_rooms(msg_in):
    to_copy = msg_in['data']

    for room in to_copy.keys():
        c.ALL_ROOMS[room] = []
        for i in msg_in[room].values():
            c.ALL_ROOMS[room].append(i)


"""
    process_user_choice prompts user to for input and verifies action is valid
    Argument: none
    Returns: str representing desired action
"""


def process_user_choice():
    valid_choices = ['$view_all$', '$create$', '$join$', '$quit$', '$leave$', '$list$', '$msg$', '$menu$']

    try:
        choice = input(f"{c.my_username} >> ")
        if not choice:
            return
        if choice.lower() not in valid_choices:
            raise ValueError
        if not choice:
            raise ValueError
    except ValueError:
        print('INVALID CHOICE ERROR: see menu')
        return 'invalid'

    return choice


"""
    establish_connection attempts to connect to server
    Arguments: none
    Returns: socket on success or none  
"""


def establish_connection(ip, port):
    try:
        c_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c_socket.connect((ip, port))
        c_socket.setblocking(False)
    except socket.error as se:
        error = base.Error()
        error.broken_connection(ip)
        error.receive()
        sys.exit(f'EXITING')

    return c_socket


"""
    manage_keepalive sets keep alive options
    Arguments: none
    Returns: socket on success or none  
"""


def manage_keepalive(c_socket):
    c_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    c_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, base.CHECK_TIME)
    c_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, base.FAIL_LIMIT)


"""
    receive msg in detects new messages and takes action based on the
    msg_in type field
    Arguments: status as True or False, True means expecting message and False means passively testing for incoming 
    message
    Returns: 0 if IO Error or Exception is hit and 1 otherwise
"""


def receive_msg_in(status, c_socket):
    try:
        while True:
            msg_in_header = c_socket.recv(base.header_len)
            header_len = len(msg_in_header)

            if not header_len:
                error = base.Error()
                error.broken_connection('SERVER')
                error.receive()
                sys.exit('EXITING')
                return False
            msg_in_len = int(msg_in_header.decode('utf-8').strip())

            if header_len > base.MSG_MAX:
                error = base.Error()
                error.msg_exceeds_len()
                error.receive()
                return False

            msg_in = c_socket.recv(msg_in_len).decode('utf-8')
            new_msg_in = json.loads(msg_in, object_hook=mm.json_msg_decoder)

            msg_status = new_msg_in.receive()
            if isinstance(new_msg_in, mm.ConnectionMessage):
                status = False
            elif isinstance(new_msg_in, mm.JoinMessage):
                if msg_status != 0:
                    print(
                        f'CLIENT ERROR, client server mismatch could not add {new_msg_in.sender} to {new_msg_in.data}')
                status = False
            elif isinstance(new_msg_in, mm.CreateRoomMessage):
                if msg_status != 1:
                    print(f'CLIENT ERROR: client server mismatch could not add {new_msg_in.data}')
                status = False
            elif isinstance(new_msg_in, base.Error):
                if msg_status == 3:
                    print(f'FATAL ERROR from Server EXITING')
                    sys.exit()
                status = True
            elif isinstance(new_msg_in, mm.ChatMessage):
                if msg_status == 0:
                    print("CLIENT ERROR: reading in chat message failed, check with Server admin")
                status = False
            elif isinstance(new_msg_in, mm.LeaveMessage):
                if msg_status != 1:
                    print(
                        f'CLIENT ERROR, client server mismatch could not remove {new_msg_in.sender}'
                        f'from {new_msg_in.data}')
                status = False
            else:
                print(f"{new_msg_in['sender']} >> {new_msg_in['type']} {new_msg_in['data']}")
    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('READ ERROR: could not read in from', str(e))
            sys.exit('EXITING')
        if status:
            return False
        else:
            return True

    return status
