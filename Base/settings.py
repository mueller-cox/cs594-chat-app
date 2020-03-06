import json


IDLE_TIME = 2  # seconds to remain idle before checking server connection
CHECK_TIME = 5  # how frequently keep alive checks connection
FAIL_LIMIT = 6  # how main times to attempt keep alive 30 seconds
JOIN_MAX = 5  # max number of rooms that can be joined
DATA_MAX = 1000  # max size of message text input
NAME_MAX = 50  # max input size for rooms and usernames
MSG_MAX = 2000  # max size of incoming messages
header_len = 20  # max size of messages
SERVER_IP = "127.0.0.1"
SERVER_PORT = 1234


class Error:
    def __init__(self, code=99, data='ERROR UNSPECIFIED'):
        self.code = code
        self.data = data

    """
       json_error converts an error object into a json object, used for sending errors to server
       Arguments: str for type of object to produce
       Returns: dictionary representation of Msg

    """

    def json_error(self):
        return dict(__type__='Error', code=self.code, data=self.data)

    """
        send_message constructs message out and sends it to the server
        Argument: socket to send on
        Returns: 0 for success or error code

    """

    def prepare_error_out(self):

        try:
            msg_out_json = json.dumps(self.json_error()).encode('utf-8')
            msg_out_header = f"{len(msg_out_json):<{header_len}}".encode('utf-8')

            if len(msg_out_json) > MSG_MAX:
                raise ValueError
        except ValueError:
            return 'ERROR: Exceeds message length limit'

        to_send = msg_out_header + msg_out_json
        return to_send

    def receive(self):
        print(f'ERROR CODE {self.code}: {self.data}')
        return self.code

    """
        modify errors for error code
    """

    def broken_connection(self, connect):
        self.code = 2
        self.data = f'CONNECTION ERROR: lost connection from {connect}'

    def create_duplicate_user(self, username):
        self.code = 3
        self.data = f'CONNECTION ERROR: {username} username already in use'

    def msg_exceeds_len(self):
        self.code = 4
        self.data = f'MSG ERROR: msg in message exceeds {MSG_MAX}'

    def empty_string(self):
        self.code = 20

        self.data = f'ERROR: empty string submitted'

    def name_exceeds_len(self):
        self.code = 21
        self.data = f'ERROR: name exceeds MAX length {NAME_MAX}'

    def create_duplicate_room(self, room):
        self.code = 25
        self.data = f'ROOM ERROR: {room} name already in use'

    def room_missing(self, room):
        self.code = 22
        self.data = f'ROOM ERROR: {room} does not exist'

    def join_duplicate_user(self, name, room):
        self.code = 24
        self.data = f'ROOM ERROR: {name} username already joined to {room}'

    def join_user_notfound(self, name, room):
        self.code = 27
        self.data = f'ROOM ERROR: {name} username not joined to {room}'

    def data_exceeds_len(self):
        self.code = 26
        self.data = f'MSG ERROR: data in message exceeds {DATA_MAX}'

    def warning_join(self):
        self.code = 28
        self.data = f'WARNING: could not join all selected rooms'

    def username_mismatch(self):
        self.code = 23
        self.data = f'USER ERROR: username does not match username associated with connection'

