import sys
import Base.settings as base
import Client.messages as mm
import Client.session as ms
import Client.settings as c


def main():
    c_socket = ms.establish_connection(base.SERVER_IP, base.SERVER_PORT)
    ms.manage_keepalive(c_socket)

    attempt_connect = 0
    action = True

    while attempt_connect == 0:
        open_msg = mm.ConnectionMessage()
        attempt_connect = open_msg.request(c_socket, 'CONNECT')

    # display intro text to user
    ms.intro()

    while True:

        out = None
        wait = True

        while action or wait:
            action = ms.receive_msg_in(action, c_socket)
            if not action:
                wait = False
            else:
                wait = True

        selection = ms.process_user_choice()

        if selection == '$create$':
            msg = mm.CreateRoomMessage(None, c.my_username, 'SERVER', None)
            status = msg.request(c_socket)
            if status:
                action = True
        elif selection == '$join$':
            msg = mm.JoinMessage(None, c.my_username, 'SERVER', None)
            num_joined = msg.request(c_socket)
            if num_joined != 0:
                warning = base.Error()
                warning.warning_join()
                warning.receive()
            action = True
        elif selection == '$view_all$':
            all_rooms = ms.list_all_rooms()
            if all_rooms != len(c.ALL_ROOMS):
                print('SYSTEM ERROR: printing all rooms')
            action = False
        elif selection == '$menu$':
            ms.intro()
            action = False
        elif selection == '$list$':
            list_mem = ms.list_room_members()
            if list_mem == -1:
                error = base.Error()
                error.room_missing('room')
                error.receive()
            action = False
        elif selection == '$msg$':
            msg = mm.ChatMessage(None, c.my_username, None, None)
            num_sent = msg.request(c_socket)
            if num_sent < 0:
                action = False
            else:
                action = True
        elif selection == '$leave$':
            msg = mm.LeaveMessage(None, c.my_username, 'Server', None)
            num_left = msg.request(c_socket)
            if num_left < 0:
                action = False
            else:
                action = True
        elif selection == '$quit$':
            msg = mm.ConnectionMessage(None, c.my_username, 'Server', None)
            msg.request(c_socket, 'QUIT')
            sys.exit('EXITED SYSTEM')

        # if there is a message to send, send it
        if out is not None:
            c_socket.send(out)


if __name__ == '__main__':
    main()
