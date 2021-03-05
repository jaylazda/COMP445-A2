"""
SERVER
"""
import socket
import select
import sys
import logging
import re
import queue
import argparse

import irc_client
import patterns

logging.basicConfig(filename='server.log', level=logging.DEBUG)
logger = logging.getLogger()


class IRCServer(patterns.Publisher):

    def __init__(self, port):
        super().__init__()
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setblocking(0)  # server won't block at server_socket.accept()
        host = 'localhost'
        self.server_socket.bind((host, port))
        self.server_socket.listen()

        # Select vars
        self.inputs = list()
        self.inputs.append(self.server_socket)
        self.outputs = list()
        self.message_queues = {}
        self.read_size = 2 ** 10

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
                        self.message_queues[r] = queue.Queue()
                        if r not in self.outputs:
                            self.outputs.append(r)
                        is_registration = re.search("^NICK\s.*;USER\s.*\s.*\s.*\s.*", data)
                        is_chat_message = re.search("^PRIVMSG\s#Global\s:.*", data)
                        # Client is sending username and nickname, server must register them
                        # Check if another client has the same username
                        if is_registration:
                            parsed_data = data.split(';')
                            nick_data, user_data = parsed_data[0].split(), parsed_data[1].split()
                            if not self.register_new_client(r, nick_data[1], user_data[1], user_data[2],
                                                            user_data[3], user_data[4]):
                                pass
                            if r not in self.outputs:
                                self.outputs.append(r)

                        # Send message to all clients on #Global channel
                        elif is_chat_message:
                            msg = data[data.index(':') + 1:]
                            self.message_queues[r].put(msg)
                            if r not in self.outputs:
                                self.outputs.append(r)
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
                        print("Broadcasting message to #Global")
                        self.send_message(w, msg)
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

    def close(self):
        """
        Close all readable sockets
        (including server socket)
        """
        # self.server_socket.close() # might not need but faced problems without it
        for s in self.inputs:
            s.close()

    def register_new_client(self, client_socket, nickname, username, host, port, real_name):
        new_client = irc_client.IRCClient(nickname=nickname, host=host, port=port)
        new_client.username = username
        logger.info(f"Client {new_client.username} connected to server")
        self.client_list.append(new_client)
        reg_msg = f'{new_client.username} joined the channel'
        self.message_queues[client_socket].put(reg_msg)
        return True

    def send_message(self, client_socket, message):
        for sock in self.inputs:
            if sock != self.server_socket and (message.endswith("joined the channel") or sock != client_socket):
                try:
                    sock.send(message.encode())
                except:
                    sock.close()
                    self.inputs.remove(sock)


def set_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', action="store", dest="port", default=8081, help="port to use, default is 8081")
    return parser


if __name__ == "__main__":
    parser = set_parser()
    args = parser.parse_args()
    server = IRCServer(args.port)
    server.run()
