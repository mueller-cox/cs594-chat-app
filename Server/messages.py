import json
import Server.settings as s
import Base.settings as base
import Base.messages as msg


class CreateRoomMessage(msg.Message):
    def __init__(self, timestamp, source, dest, data):
        super(CreateRoomMessage, self).__init__(timestamp, source, dest, data)

    """receive processes incoming create requests from client: calls validate to see if room can be created, 
    adds room to ROOMS dictionary, adds room to OWNERS dictionary, and room to JOINED dictionary that tracks users who 
    belong to a room , creates outgoing message to send to user about room creation
    Arguments: incoming message, outgoing message template, user name, client socket
    Returns: room_name that was created or None
    """

    def receive(self, c_socket):
        valid_name = self.validate_room_creation()
        if valid_name == 0:
            room_name = self.data
            s.ROOMS[room_name] = []
            s.OWNERS[room_name] = self.sender
            s.JOINED[room_name] = []
            created = True
        else:
            error_out = base.Error()
            if valid_name == 20:
                error_out.empty_string()
            elif valid_name == 25:
                error_out.create_duplicate_room(self.data)
            elif valid_name == 21:
                error_out.name_exceeds_len()
            to_send = error_out.prepare_error_out()
            c_socket.send(to_send)
            created = False

        return created

    """
        request sends create request messages to all logged in clients
        Arguments: none
        Returns: none
    """

    def request(self):
        new_msg = CreateRoomMessage(None, 'SERVER', 'ALL', self.data)
        to_send = new_msg.prepare_msg_out('CreateRoomMessage')
        for clients in s.CLIENTS:
            clients.send(to_send)

    """
        validate_room_creation verifies if room can be created
        Arguments: none
        Returns: int that corresponds to error code or 0 if valid
    """

    def validate_room_creation(self):
        try:
            if not self.data:
                raise ValueError(20)

            if len(self.data) > base.NAME_MAX:
                raise ValueError(21)

            adjusted_name = self.data.lower()

            if adjusted_name in s.ROOMS:
                raise ValueError(25)

        except ValueError as ve:
            return ve

        return 0


class ConnectionMessage(msg.Message):
    def __init__(self, timestamp, source, dest, data):
        super(ConnectionMessage, self).__init__(timestamp, source, dest, data)

    """
        request sends a connection message to a client or clients
        Arguments: socket of client 
        Returns: none
        
    """

    def request(self, c_socket):
        to_send = self.prepare_msg_out('ConnectionMessage')
        c_socket.send(to_send)

    """
        receive_connect processes an incoming connection message if data in message is CONNECT and message is valid
        Arguments: c_socket
        Returns: True if connect can be processes and False otherwise
    """

    def receive_connect(self, c_socket):
        is_valid = self.validate_username(self.sender)

        if is_valid == 0:
            s.SOCKETS_LIST.append(c_socket)
            s.CLIENTS[c_socket] = self.sender

            # send user successful connection message
            msg_out = ConnectionMessage(None, 'SERVER', self.sender, 'CONNECTED')
            to_send = msg_out.prepare_msg_out('ConnectionMessage')
            c_socket.send(to_send)

            # send user all of the existing rooms and users joined to the rooms
            for rooms in s.JOINED.keys():
                create = CreateRoomMessage(None, 'Server', self.sender, rooms)
                to_send = create.prepare_msg_out('CreateRoomMessage')
                c_socket.send(to_send)
                for user in s.JOINED[rooms]:
                    join = JoinMessage(None, user, self.sender, rooms)
                    to_send = join.prepare_msg_out('JoinMessage')
                    c_socket.send(to_send)

            added = True
        else:
            error_out = base.Error()
            if is_valid == 20:
                error_out.empty_string()
            elif is_valid == 3:
                error_out.create_duplicate_user(self.sender)
            elif is_valid == 21:
                error_out.name_exceeds_len()
            to_send = error_out.prepare_error_out()
            c_socket.send(to_send)
            added = False

        return added

    """
        verifies if username is valid (empty string, too long, or already in use)
        Argument: str of name
        Returns: 0 if valid or error code if invalid
    """

    @staticmethod
    def validate_username(name_in):

        if not name_in:
            return 20
        if len(name_in) > base.NAME_MAX:
            return 21
        for sock in s.CLIENTS.keys():
            if name_in == s.CLIENTS[sock]:
                return 3

        return 0


class JoinMessage(msg.Message):
    def __init__(self, timestamp, source, dest, data):
        super(JoinMessage, self).__init__(timestamp, source, dest, data)

    """
        join_room processes incoming join request from client: call join validation, and if valid sends success message to
        requester and adds user to JOIN dictionary
        Arguments: incoming message, outgoing message template, user name, client socket
        Returns: None or name of room joined
    """

    def receive(self, c_socket):
        valid_join = self.validate_join_request(self.sender, self.data)

        if valid_join == 0:
            room = self.data
            s.JOINED[room].append(self.sender)
            joined = True
        else:
            send_error = base.Error()
            if valid_join == 20:
                send_error.empty_string()
            elif valid_join == 24:
                send_error.join_duplicate_user(self.sender, self.data)
            elif valid_join == 21:
                send_error.name_exceeds_len()
            elif valid_join == 22:
                send_error.room_missing(self.data)
            to_send = send_error.prepare_error_out()
            c_socket.send(to_send)
            joined = False
        return joined

    """
        validation_join_request verifies if room can be joined
        Arguments: str of room name to be created
        Returns: str dependent on join request can be done
    """

    @staticmethod
    def validate_join_request(username, room):

        if not room or not username:
            return 20

        if len(username) > base.NAME_MAX or len(room) > base.NAME_MAX:
            return 21

        if room not in s.ROOMS.keys():
            return 22

        if username in s.JOINED[room]:
            return 24

        return 0

    """
        request sends join messages to all clients to update their ALL ROOMS list with new member and sends the most
        recent 10 messages to the joining user
        Argument: c_socket
        Returns: nothing 
    """

    def request(self, c_socket):

        to_all = JoinMessage(None, self.sender, 'ALL', self.data)
        to_send = to_all.prepare_msg_out('JoinMessage')

        # send join message to all clients
        for clients in s.CLIENTS:
            clients.send(to_send)

        # send 10 most recent msgs for room to sender, if there are no messages do nothing
        if len(s.ROOMS[self.data]) >= 10:
            for msgs in s.ROOMS[self.data][-10:]:
                to_send = msgs.prepare_msg_out('ChatMessage')
                c_socket.send(to_send)
        elif len(s.ROOMS[self.data]) > 0:
            for msgs in s.ROOMS[self.data]:
                to_send = msgs.prepare_msg_out('ChatMessage')
                c_socket.send(to_send)


class ChatMessage(msg.Message):

    def __init__(self, timestamp, source, dest, data):
        super(ChatMessage, self).__init__(timestamp, source, dest, data)

    """
        receive called when server receives a message of type MSG adds MSG to appropriate rooms
        Argument: none
        Returns: True if message could be added or False if error was sent to sender
    """

    def receive(self, c_socket):

        valid_room = self.validate_room_name(self.dest)
        valid_data = False

        if len(self.data) <= base.DATA_MAX:
            valid_data = True

        if valid_room == 0 and valid_data:
            s.ROOMS[self.dest].append(self)
            msg_ok = True
        else:
            error_out = base.Error()
            if valid_room == 20:
                error_out.empty_string()
            elif valid_room == 25:
                error_out.room_missing(self.dest)
            elif valid_room == 21:
                error_out.name_exceeds_len()
            elif valid_data is False:
                error_out.data_exceeds_len()
            to_send = error_out.prepare_error_out()
            c_socket.send(to_send)
            msg_ok = False
        return msg_ok

    """
        validate_room_name checks if room exists and if the name provided meets expectations, if not, returns error code
        Argument: str for room_name
        Returns: int of error code or 0 if valid
    """
    @staticmethod
    def validate_room_name(room_name):
        try:
            if not room_name:
                raise ValueError(20)

            if len(room_name) > base.NAME_MAX:
                raise ValueError(21)

            adjusted_name = room_name.lower()

            if adjusted_name not in s.ROOMS:
                raise ValueError(25)

        except ValueError as ve:
            return ve

        return 0

    """
        forward sends msgs out to all users who have joined the associated room
        Arguments: none
        Returns: none
    """
    def forward(self):
        to_send = self.prepare_msg_out('ChatMessage')

        for user in s.JOINED[self.dest]:
            for client in s.CLIENTS.keys():
                if user == s.CLIENTS[client]:
                    client.send(to_send)


class LeaveMessage(msg.Message):
    def __init__(self, timestamp, source, dest, data):
        super(LeaveMessage, self).__init__(timestamp, source, dest, data)

    """
        receive processes incoming leave request from client: calls leave validation, and if valid removes user from 
        associated room in JOINS list
        Arguments: client socket
        Returns: True if leave successful and False otherwise
    """

    def receive(self, c_socket):
        valid_leave = self.validate_leave_request(self.data, self.sender)

        if valid_leave == 0:
            s.JOINED[self.data].remove(self.sender)
            left = True
        else:
            send_error = base.Error()
            if valid_leave == 20:
                send_error.empty_string()
            elif valid_leave == 27:
                send_error.join_duplicate_user(self.sender, self.data)
            elif valid_leave == 21:
                send_error.name_exceeds_len()
            elif valid_leave == 22:
                send_error.room_missing(self.data)
            to_send = send_error.prepare_error_out()
            c_socket.send(to_send)
            left = False

        return left

    """
        validate_leave_request verifies if room can be left
        Arguments: str of room name to be removed
        Returns: str dependent on whether leave request can be done
    """

    @staticmethod
    def validate_leave_request(room_name, username):

        if not room_name or not username:
            return 20

        if len(username) > base.NAME_MAX or len(room_name) > base.NAME_MAX:
            return 21

        if room_name not in s.ROOMS.keys():
            return 22

        if username not in s.JOINED[room_name]:
            return 27

        return 0

    """
        request sends a leave request to all clients
        Arguments: none
        Returns: none
    """
    def request(self):
        to_send = self.prepare_msg_out('LeaveMessage')
        # send join message to all clients
        for clients in s.CLIENTS:
            clients.send(to_send)



"""
    json_obj_decode converts a json object into a python object
    Argument: json object to decode
    Returns: python object
"""


def json_obj_decoder(to_decode):
    if '__type__' in to_decode and to_decode['__type__'] == 'Message':
        return msg.Message(to_decode['timestamp'], to_decode['sender'], to_decode['dest'], to_decode['data'])
    if '__type__' in to_decode and to_decode['__type__'] == 'CreateRoomMessage':
        return CreateRoomMessage(to_decode['timestamp'], to_decode['sender'], to_decode['dest'], to_decode['data'])
    if '__type__' in to_decode and to_decode['__type__'] == 'ConnectionMessage':
        return ConnectionMessage(to_decode['timestamp'], to_decode['sender'], to_decode['dest'], to_decode['data'])
    if '__type__' in to_decode and to_decode['__type__'] == 'JoinMessage':
        return JoinMessage(to_decode['timestamp'], to_decode['sender'], to_decode['dest'], to_decode['data'])
    if '__type__' in to_decode and to_decode['__type__'] == 'ChatMessage':
        return ChatMessage(to_decode['timestamp'], to_decode['sender'], to_decode['dest'], to_decode['data'])
    if '__type__' in to_decode and to_decode['__type__'] == 'LeaveMessage':
        return LeaveMessage(to_decode['timestamp'], to_decode['sender'], to_decode['dest'], to_decode['data'])
    return to_decode
