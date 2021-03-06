import Client.settings as c
import Base.settings as base
import Base.messages as msg


class CreateRoomMessage(msg.Message):
    def __init__(self, timestamp, sender, dest, data):
        super(CreateRoomMessage, self).__init__(timestamp, sender, dest, data)

    """
         prompts user to input name of room they wish to create
         errors on empty string, if not empty then sends CREATE
         request to Server
    """

    def request(self, c_socket):

        try:
            my_room = input("New room name: ")
            error = base.Error()
            if not my_room:
                error.empty_string()
                raise ValueError
            if my_room in c.ALL_ROOMS:
                error.create_duplicate_room(my_room)
                raise ValueError
            if len(my_room) > base.NAME_MAX:
                error.name_exceeds_len()
                raise ValueError
        except ValueError as e:
            error.receive()
            return False

        self.data = my_room.rstrip()

        msg_out = self.prepare_msg_out('CreateRoomMessage')
        c_socket.send(msg_out)
        return True

    """
        receive updates ALL_ROOMS list
        and appends the msg_in data as a new entry
        returns 1 if the item could be added and 0 otherwise
        will not add an room one already exists
    """

    def receive(self):
        new_room = self.data

        if new_room is None:
            return 0

        if new_room in c.ALL_ROOMS.keys():
            return 0

        c.ALL_ROOMS[new_room] = []
        return 1


class JoinMessage(msg.Message):
    def __init__(self, timestamp, sender, dest, data):
        super(JoinMessage, self).__init__(timestamp, sender, dest, data)

    """
        prompts user to input name of room they wish to create
        errors on empty string, if not empty then sends CREATE
        request to Server
    """

    def request(self, c_socket):
        num_joined = 0
        try:
            error = base.Error()
            my_join_request = input("What room(s) do you wish to join? comma separated list for multiple joins: ")
            if not my_join_request:
                error.empty_string()
                raise ValueError

            adjust_join = my_join_request.lower()
            join_list = adjust_join.split(",")
        except ValueError:
            error.receive()
            return -1

        for room in join_list:
            if room in c.ALL_ROOMS.keys():
                if room not in c.MY_ROOMS.keys():
                    self.data = room.rstrip()
                    to_send = self.prepare_msg_out('JoinMessage')
                    c_socket.send(to_send)
                    num_joined += 1
                else:
                    error = base.Error()
                    error.join_duplicate_user(c.my_username,room)
                    error.receive()
            else:
                error = base.Error()
                error.room_missing(room)
                error.receive()

        return len(join_list) - num_joined

    """
        receive_join_message checks that join is valid and if so, updates ALL_ROOMS
        if the sender is the same as the user this function also results in the MY_ROOMS dictionary being updated
        Arguments: none
        Returns: int representing Error or Success 0 is success
    """

    def receive(self):
        to_add = self.sender
        room = self.data

        if to_add is None or room is None:
            return 20

        if room not in c.ALL_ROOMS.keys():
            return 22

        if to_add in c.ALL_ROOMS[room]:
            return 24

        if room in c.MY_ROOMS.keys() and self.sender == c.my_username:
            return 24

        c.ALL_ROOMS[room].append(to_add)

        if to_add == c.my_username:
            c.MY_ROOMS[room] = []

        return 0


class ChatMessage(msg.Message):
    def __init__(self, timestamp, sender, dest, data):
        super(ChatMessage, self).__init__(timestamp, sender, dest, data)
    """
        choose_destination prompts user to select which rooms to send to (must be joined to send)
        entering all will send to all joined
        Argument: none
        Returns: list of recipients (str)
    """

    @staticmethod
    def choose_recipients():
        print("Enter rooms to message as comma separated list (must be joined to send)")
        adjusted = ""
        try:
            my_recipients = input("Rooms to msg: ")
            error = base.Error()

            if not my_recipients:
                error.empty_string()
                raise ValueError

            adjusted = my_recipients.lower()
            adjusted = my_recipients.split(',')

            for room in adjusted:
                if room not in c.MY_ROOMS.keys():
                    adjusted.remove(room)
                    error.room_missing(room)
                    raise ValueError
        except ValueError:
            error.receive()

        return adjusted

    """
        send_message creates message and sends to rooms, calls choose recipient 
        Argument: client socket to send from
        Returns: 1 if message sent and 0 otherwise
    """

    def request(self, c_socket):
        num_sent = 0

        recipients = self.choose_recipients()

        if len(recipients) < 1:
            return -1

        try:
            my_msg = input("Msg: ")
            error = base.Error()
            if not my_msg:
                error.empty_string()
                raise ValueError
            if len(my_msg) > base.MSG_MAX:
                error.data_exceeds_len()
                raise ValueError
        except ValueError:

            error.receive()

            return -1

        self.data = my_msg

        for room in recipients:
            self.dest = room.rstrip()
            to_send = self.prepare_msg_out('ChatMessage')
            c_socket.send(to_send)
            num_sent += 1

        return len(recipients) - num_sent

    """
        receive appends message to corresponding MY_ROOMS
        returns 1 if MY_ROOMS could be updated and 0 otherwise
    """

    def receive(self):
        room = self.dest

        if room is None:
            return 0

        if room not in c.MY_ROOMS.keys():
            return 0

        c.MY_ROOMS[room].append(self)

        print(f"[ROOM: {room}] >> {self.sender} >> {self.timestamp} >> {self.data}")

        return 1


class LeaveMessage(msg.Message):
    def __init__(self, timestamp, sender, dest, data):
        super(LeaveMessage, self).__init__(timestamp, sender, dest, data)

    """
        request_leave_room deletes room or rooms from MY_ROOMS and sends a message to server for each room that is left
        Argument: client socket, msg_out template
        Returns: 1 if rooms could be left and 0 otherwise
    """

    def request(self, c_socket):
        num_left = 0

        try:
            my_leave_request = input("What room(s) do you wish to leave? comma separated list for multiple joins: ")
            if not my_leave_request:
                raise ValueError

            adjust_leave = my_leave_request.lower()
            leave_list = adjust_leave.split(",")

        except ValueError as e:
            error = base.Error()
            error.empty_string()
            error.receive()
            return -1

        for room in leave_list:
            if room in c.MY_ROOMS.keys():
                del c.MY_ROOMS[room]
                self.data = room.rstrip()
                to_send = self.prepare_msg_out('LeaveMessage')
                c_socket.send(to_send)
                num_left += 1
            else:
                error = base.Error()
                error.room_missing(room)
                error.receive()

        return len(leave_list) - num_left

    """
        receive updates ALL_ROOMS dictionary
        and removes the user from the corresponding key
        returns 1 if dictionary could be updated and 0 otherwise

    """

    def receive(self):
        member = self.sender
        room = self.data

        if member is None:
            return 0
        if room not in c.ALL_ROOMS.keys():
            return 0
        if member not in c.ALL_ROOMS[room]:
            return 0

        c.ALL_ROOMS[room].remove(member)
        return 1


class ConnectionMessage(msg.Message):
    def __init__(self, timestamp=None, sender=None, dest='SERVER', data=None):
        super(ConnectionMessage, self).__init__(timestamp, sender, dest, data)
    """
        request_quit sends a quit message to server and closes the client session
        Argument: client socket, msg_out template
        Returns: 1 if roo
    """

    def request(self, c_socket, data):
        if data is None:
            return 0

        if data == 'CONNECT':
            self.data = data
            msg_out = self.request_open()
        elif data == 'QUIT':
            self.data = data
            msg_out = self.request_close()
        else:
            return 0

        if msg_out is None:
            return 0

        c_socket.send(msg_out)

        return 1

    """
        request_open creates and sends initial connection message to server
        Arguments: none
        Returns: byte str of message to send or None
    """

    def request_open(self):
        try:
            from_user = input("Username: ")
            error = base.Error()

            if not from_user:
                error.empty_string()
                raise ValueError
            elif len(from_user) > base.NAME_MAX:
                error.name_exceeds_len()
                raise ValueError
            c.my_username = from_user.lower().rstrip()
        except ValueError:
            error.receive()
            return None

        self.sender = c.my_username.rstrip()
        to_send = self.prepare_msg_out('ConnectionMessage')
        return to_send

    """
        request_close send quit message to server 
        Arguments: none
        Returns: str message to send 
    """

    def request_close(self):
        to_send = self.prepare_msg_out('ConnectionMessage')
        return to_send

    """
        receive processes connection messages from server, either acknowledges
        an open connection or terminates session
        Arugments: none
        Returns: True or False on whether connection should continue
    """

    def receive(self):
        if self.data == 'CONNECT':
            print('Successfully connected to Server')
            return True

        elif self.data == 'QUIT':
            print('Server has shutdown, connection is lost. Closing Client App Now')
            return False


"""
    json_obj_decode converts a json object into a python object
    Argument: json object to decode
    Returns: python object
"""


def json_msg_decoder(to_decode):
    if '__type__' in to_decode and to_decode['__type__'] == 'Message':
        return msg.Message(to_decode['timestamp'], to_decode['sender'], to_decode['dest'], to_decode['data'])
    if '__type__' in to_decode and to_decode['__type__'] == 'CreateRoomMessage':
        return CreateRoomMessage(to_decode['timestamp'], to_decode['sender'], to_decode['dest'], to_decode['data'])
    if '__type__' in to_decode and to_decode['__type__'] == 'JoinMessage':
        return JoinMessage(to_decode['timestamp'], to_decode['sender'], to_decode['dest'], to_decode['data'])
    if '__type__' in to_decode and to_decode['__type__'] == 'ConnectionMessage':
        return ConnectionMessage(to_decode['timestamp'], to_decode['sender'], to_decode['dest'], to_decode['data'])
    if '__type__' in to_decode and to_decode['__type__'] == 'LeaveMessage':
        return LeaveMessage(to_decode['timestamp'], to_decode['sender'], to_decode['dest'], to_decode['data'])
    if '__type__' in to_decode and to_decode['__type__'] == 'ChatMessage':
        return ChatMessage(to_decode['timestamp'], to_decode['sender'], to_decode['dest'], to_decode['data'])
    if '__type__' in to_decode and to_decode['__type__'] == 'Error':
        return base.Error(to_decode['code'], to_decode['data'])
    return to_decode
