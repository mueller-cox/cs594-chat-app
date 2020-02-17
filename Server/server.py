import socket
import sys
import select
from threading import Thread

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234

# initialize server listening port
s_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s_socket.bind((IP, PORT))
s_socket.listen(5)


sockets_list = [s_socket]  # list of connected sockets
clients = {}  # associate socket info with client name


def main():
    print("Waiting for client connection...")
    connect_thread = Thread(target=handle_incoming_connections)
    connect_thread.start()
    connect_thread.join()
    s_socket.close()


def handle_incoming_connections():
    while True:
        c_socket, c_address = s_socket.accept()
        user = receive_message(c_socket)
        if user is False:
            continue
        sockets_list.append(c_socket)
        clients[c_socket] = user
        print(f"New connection from {c_address[0]}:{c_address[1]} username:{user['data'].decode('utf-8')}")
        Thread(target=manage_client, args=(c_socket,)).start()


def receive_message(c_socket):
    try:
        message_header = c_socket.recv(HEADER_LENGTH)

        if not len(message_header):
            return False
        message_len = int(message_header.decode('utf-8').strip())
        return {"header": message_header, "data": c_socket.recv(message_len)}

    except:
        return False


def manage_client(c_socket):
    while True:
        message = receive_message(c_socket)

        if message is False:
            print(f"Closed connection from {clients[c_socket]['data'].decode('utf-8')}")
            sockets_list.remove(c_socket)
            del clients[c_socket]
            continue

        user = clients[c_socket]
        print(f"Received message from {user['data'].decode('utf-8')}: {message['data'].decode('utf-8')}")

        for client_socket in clients:
            if client_socket != c_socket:
                client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])


if __name__ == '__main__':
    main()
