import Server.settings as s
import Server.messages as msg


"""
    when a user exits remove them from joined, send leave messages for each room joined to, remove from sockets list,
    and clients list then close socket
"""


def process_client_exit(c_socket, username):
    for room in s.JOINED.keys():
        if username in s.JOINED[room]:
            leave = msg.LeaveMessage(None, username, 'ALL', room)
            leave.request()
            s.JOINED[room].remove(username)

    if c_socket in s.SOCKETS_LIST:
        s.SOCKETS_LIST.remove(c_socket)

    if c_socket in s.CLIENTS.keys():
        del s.CLIENTS[c_socket]
    c_socket.close()
