import Base.settings as base
from datetime import datetime
import json


class Message(object):
    def __init__(self, timestamp=None, sender=None, dest=None, data=None):
        if timestamp is None:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.timestamp = timestamp
        self.sender = sender
        self.dest = dest
        self.data = data

    """
        json_msg converts a message object into a json object, used for sending messages to server
        Arguments: str for type of message to create
        Returns: dictonary representation of Msg

    """

    def json_msg(self, type_str):
        return dict(__type__=type_str, timestamp=self.timestamp, dest=self.dest, sender=self.sender, data=self.data)

    """
        send_message constructs message out and sends it to the server
        Argument: str of type of message that is being prepared
        Returns: 0 for success or error code

    """

    def prepare_msg_out(self, type_str):
        try:
            msg_out_json = json.dumps(self.json_msg(type_str)).encode('utf-8')
            msg_out_header = f"{len(msg_out_json):<{base.header_len}}".encode('utf-8')

            if len(msg_out_json) > base.MSG_MAX:
                raise ValueError
            to_send = msg_out_header + msg_out_json

            return to_send
        except ValueError:
            return
