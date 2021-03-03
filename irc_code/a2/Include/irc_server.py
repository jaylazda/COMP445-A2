"""
SERVER
"""
import socket
import select
import sys
import logging
import re
import queue

import irc_client
import patterns

logging.basicConfig(filename='server.log', level=logging.DEBUG)
logger = logging.getLogger()

class IRCServer(patterns.Publisher):

    def __init__(self, port):
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setblocking(0) #server won't block at server_socket.accept()
        host = 'localhost'
        self.server_socket.bind((host, port))
        self.server_socket.listen()

        #Select vars
        self.inputs = list()
        self.inputs.append(self.server_socket)
        self.outputs = list()
        self.message_queues = {}
        self.outbox = dict()
        self.messages = dict()
        self.read_size = 2**10

        self.client_list = list()

    def run(self):
        print(f"Running server at localhost:{self.port}")
        logger.info(f"Running server at localhost:{self.port}")
        try:
            while True:
                readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs)
                for r in readable:
                    # Server socket accepting clients
                    # Add client to client_list, add client to global channel?
                    if r is self.server_socket:
                        client_socket, addr = r.accept()
                        client_socket.setblocking(0)
                        self.inputs.append(client_socket)
                        self.message_queues[r] = queue.Queue()

                        print(f"New client @ {addr}")
                        logger.info(f"New client @ {addr}")
                    # Reading from clients
                    else:
                        data = r.recv(self.read_size).decode('utf-8')
                        print(f"Received {data} from {r.getpeername()}")
                        print(f"Message_queues is \n{self.message_queues}")
                        #self.message_queues[r] = queue.Queue()
                        self.message_queues[r].put(data)
                        if r not in self.outputs:
                            self.outputs.append(r)
                        # is_nick_and_user = re.search("^NICK\s.*;USER\s.*\s.*\s.*\s.*", data)
                        # is_chat_message = re.search("^PRIVMSG\s#Global\s:.*", data)
                        # # Client is sending username and nickname, server must register them
                        # if is_nick_and_user:
                        #     parsed_data = data.split(';')
                        #     nick_data, user_data = parsed_data[0].split(), parsed_data[1].split()
                        #     nick = nick_data[1]
                        #     new_client = irc_client.IRCClient(nickname=nick, host=user_data[2], port=user_data[3])
                        #     new_client.username = user_data[1]
                        #     print(f"Client username is {new_client.username}")
                        #     logger.info(f"Client {new_client.username} connected to server")
                        #     self.client_list.append(new_client)
                        #     reg_msg = f'{new_client.username} added to channel #Global'
                        #
                        #     self.outbox[r] = reg_msg
                        #     if r not in self.outputs:
                        #         self.outputs.append(r)
                        #     #self.subscribers.append(new_client)
                        # # Send message to all clients on #Global channel
                        # elif is_chat_message:
                        #     message = data[data.index(':')+1:]
                        #     self.messages[r] += message
                        #     if r not in self.outputs:
                        #         self.outputs.append(r)
                        #     # self.messages[r] += message
                        # Data is empty
                        else:
                            self.inputs.remove(r)
                            if r in self.outputs:
                                self.outputs.remove(r)
                            r.close()
                            print(f"Closed a client socket: {r}")
                            logger.info(f"Closed a client socket: {r}")
                            del self.message_queues[r]
                for w in writable:
                    try:
                        msg = self.message_queues[w].get_nowait()
                    except KeyError:
                        print(f"Client connection was closed")
                    except queue.Empty:
                        print(f"Output queue for {w.getpeername()} is empty")
                        self.outputs.remove(w)
                    else:
                        print(f"Sending {msg} to {w.getpeername()}")
                        w.send(msg.encode())
                    # msg = self.outbox[w]
                    # if len(msg):
                    #     logger.info(f'Sending {msg} to {w.getpeername()}')
                    #     w.send(msg.encode())
                    #     self._clear_outbox(w)
                    #self.potential_writes.remove(w)
                for err in exceptional:
                    print(f'Handling exception for {err.getpeername()}')
                    self.inputs.remove(err)
                    if err in self.outputs:
                        self.outputs.remove(err)
                    err.close()
                    del self.message_queues[err]

        except KeyboardInterrupt:
            print(f"\nServer interrupted, closing socket connections")
            self.close()

    def _clear_outbox(self, client_socket):
        if client_socket in self.outbox:
            self.outbox[client_socket] = str()

    def close(self):
        """
        Close all readable sockets
        (including server socket)
        """
        # self.server_socket.close() # might not need but faced problems without it
        for s in self.inputs:
            s.close()

    def _parse_message(self, client):
        """
        If message is bigger than the read size then it must be broken up
        """
        pass

    def add_client_to_channel(self, client):
        """
        Add client to #global channel upon successful client connection/registration
        """
        pass

if __name__ == "__main__":
    server_port = 8081
    if len(sys.argv) > 2:
        print('You have specified too many arguments')
        sys.exit()
    elif len(sys.argv) == 1:
        pass
    elif sys.argv[1] == '--help' or sys.argv[1] == '-h':
        print('\nusage: irc_server.py [-h] [PORT]\nDefaults to port: 8081 if not'
              'specified \n\noptional arguments:\n  -h, --help\t  Show this help message and exit\n  --port PORT\t  Port to use')
        sys.exit()
    elif str(sys.argv[1]).isdigit():
        server_port = sys.argv[1]
    server = IRCServer(server_port)
    server.run()