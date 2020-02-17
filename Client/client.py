import socket
import errno
import sys

SERVER_IP = "127.0.0.1"
SERVER_PORT = 1234
MSG_BUF_SIZE = 1024
HEADER_LENGTH = 10

my_username = input("Username: ")
c_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c_socket.connect((SERVER_IP, SERVER_PORT))
c_socket.setblocking(False)

username = my_username.encode('utf-8')
username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
c_socket.send(username_header + username)

while True:
    message_out = input(f"{my_username} >> ")

    if message_out:
        message_out = message_out.encode('utf-8')
        message_header = f"{len(message_out) :< {HEADER_LENGTH}}".encode('utf-8')
        c_socket.send(message_header + message_out)

    try:
        while True:
            username_in_header = c_socket.recv(HEADER_LENGTH)
            if not len(username_in_header):
                print("server closed connection")
                sys.exit()
            username_in_len = int(username_in_header.decode('utf-8').strip())
            username_in = c_socket.recv(username_in_len).decode('utf-8')

            msg_in_header = c_socket.recv(HEADER_LENGTH)
            msg_in_len = int(msg_in_header.decode('utf-8').strip())
            msg_in = c_socket.recv(msg_in_len).decode('utf-8')
            print(f"{username_in} >> {msg_in}")

    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('error reading in from', str(e))
            sys.exit()
        continue

    except Exception as e:
        print('General error', str(e))
        sys.exit()

