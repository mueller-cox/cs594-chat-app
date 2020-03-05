import sys
sys.path.insert(1, '/ChatApp/')
from threading import Thread
import Server.messages as mr
import Server.session as sess
import Server.settings as s
import Base.settings as base
import socket
import json
import sys

#  initialize server listening port
S_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
S_SOCKET.bind((base.SERVER_IP, base.SERVER_PORT))
S_SOCKET.listen(5)

s.SOCKETS_LIST.append(S_SOCKET)  # list of connected sockets


def main():
    print("Waiting for client connection...")
    try:
        connect_thread = Thread(target=handle_incoming_connections)
        connect_thread.start()
        connect_thread.join()
        S_SOCKET.close()
    except KeyboardInterrupt:
        connect_thread.join()
        S_SOCKET.close()
        sys.exit('EXITING Server system is shutting down')


"""
    handle_incoming_connections manages new connections from from client apps
    Arguments:
    Returns:
"""


def handle_incoming_connections():
    while True:
        c_socket, c_address = S_SOCKET.accept()
        user = receive_message(c_socket)
        if not user:
            continue
        elif isinstance(user, mr.ConnectionMessage):
            if user.data == 'CONNECT':
                success = user.receive_connect(c_socket)
                if success:
                    print(f"New connection from {c_address[0]}:{c_address[1]} username: {user.sender}")
                    Thread(target=manage_client, args=(c_socket,)).start()
                else:
                    print(f"Connection refused from {c_address[0]}:{c_address[1]} username: {user.sender}")
                    continue


"""
    receive_message manages receiving messages from client apps
    Argument: client socket with incoming message
    Returns: new message as string or None
"""


def receive_message(c_socket):
    try:
        message_header = c_socket.recv(base.header_len)

        if not len(message_header):
            return False
        message_len = int(message_header.decode('utf-8').strip())
        msg_in = c_socket.recv(message_len).decode('utf-8')
        new_msg = json.loads(msg_in, object_hook=mr.json_obj_decoder)
        return new_msg
    except ValueError:
        print('INTERNAL ERROR: value error loading received message')
        return False
    except socket.error:
        return False
    except KeyError:
        return False


"""
    manage_client manages a logged in user's client session this involves incoming and outgoing join, create, and message
    requests and responses
    Argument: client socket 
    Returns:
"""


def manage_client(c_socket):
    run = True
    while run:
        try:
            msg_in = receive_message(c_socket)

            if msg_in is False:
                print(f"Closed connection from {s.CLIENTS[c_socket]}")
                sess.process_client_exit(c_socket, s.CLIENTS[c_socket])
                run = False
                continue
        except socket.error:
            print(f'ERROR socket error from {c_socket}')
            sess.process_client_exit(c_socket, s.CLIENTS[c_socket])
            run = False
        except KeyboardInterrupt:
            print(f'Exception keyboard interupt from {c_socket}')
            sess.process_client_exit(c_socket, s.CLIENTS[c_socket])
            run = False
        except KeyError:
            print(f'Exception key error from {c_socket}')
            sess.process_client_exit(c_socket, s.CLIENTS[c_socket])
            run = False

        user = s.CLIENTS[c_socket]

        print(f"Received {type(msg_in)} message from {user}: {msg_in.data}")
        try:
            if isinstance(msg_in, mr.CreateRoomMessage):
                created = msg_in.receive(c_socket)
                if created:
                    msg_in.request()
            elif isinstance(msg_in, mr.JoinMessage):
                joined = msg_in.receive(c_socket)
                if joined:
                    msg_in.request(c_socket)
            elif isinstance(msg_in, mr.ChatMessage):
                sent = msg_in.receive(c_socket)
                if sent:
                    msg_in.forward()
            elif isinstance(msg_in, mr.LeaveMessage):
                left = msg_in.receive(c_socket)
                if left:
                    msg_in.request()
            elif isinstance(msg_in, mr.ConnectionMessage):
                if msg_in.data == 'QUIT':
                    sess.process_client_exit(c_socket, msg_in.sender)
                    run = False
            else:
                continue
        except socket.error:
            print("INTERNAL ERROR CLIENT WILL EXIT")
            run = False


if __name__ == '__main__':
    main()
