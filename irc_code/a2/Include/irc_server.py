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
        self.potential_reads = list()
        self.potential_reads.append(self.server_socket)
        self.potential_writes = list()
        self.potential_errors = list()
        self.queued_messages = dict()
        self.messages = dict()
        self.read_size = 2**10

        self.client_list = list()

    def run(self):
        print(f"Running server at localhost:{self.port}")
        logger.info(f"Running server at localhost:{self.port}")
        try:
            while True:
                r_reads, r_writes, r_errors = select.select(self.potential_reads, self.potential_writes, self.potential_errors)
                for r in r_reads:
                   
                    # Server socket accepting clients
                    # Add client to client_list, add client to global channel?
                    if r is self.server_socket:
                        client_socket, addr = r.accept()
                        client_socket.setblocking(0)
                        print(f"New client @ {addr}")
                        logger.info(f"New client @ {addr}")
                        self.queued_messages[client_socket] = queue.Queue()
                        self.messages[client_socket] = str()
                        self.potential_reads.append(client_socket)
                        self.potential_writes.append(client_socket)
                    # Reading from clients
                    else:
                        data = r.recv(self.read_size).decode('utf-8')
                        is_nick_and_user = re.search("^NICK\s.*;USER\s.*\s.*\s.*\s.*", data)
                        is_chat_message = re.search("^PRIVMSG\s#Global\s:.*", data)
                        # Client is sending username and nickname, server must register them
                        if is_nick_and_user:
                            parsed_data = data.split(';')
                            nick_data, user_data = parsed_data[0].split(), parsed_data[1].split()
                            nick = nick_data[1]
                            new_client = irc_client.IRCClient()
                            new_client.username = user_data[1]
                            print(f"Client username is {new_client.username}")
                            logger.info(f"Client {new_client.username} connected to server")
                            self.client_list.append(new_client)
                            reg_msg = f'{new_client.username} added to channel #Global'
                            self.queued_messages[r].put(reg_msg)
                            if r not in self.potential_writes:
                                self.potential_writes.append(r)
                            #self.subscribers.append(new_client)
                        # Send message to all clients on #Global channel
                        elif is_chat_message:
                            message = data[data.index(':')+1:]
                            self.queued_messages[r].put(message)
                            if r not in self.potential_writes:
                                self.potential_writes.append(r)
                            # self.messages[r] += message
                        # Data is empty
                        else:
                            self.potential_reads.remove(r)
                            if r in self.potential_writes:
                                self.potential_writes.remove(r)
                            r.close()
                            print(f"Closed a client socket: {r}")
                            logger.info(f"Closed a client socket: {r}")
                            if r in self.queued_messages:
                                del self.queued_messages[r]
                            if r in self.messages:
                                del self.messages[r]
                for w in r_writes:
                    try:
                        msg = self.queued_messages[w].get_nowait()
                    except queue.Empty:
                        # No messages waiting so stop checkin for writability
                        logger.error(f'Output queue for {w.getpeername()} is empty')
                        self.potential_writes.remove(w)
                    else:
                        logger.info(f'Sending {msg} to {w.getpeername()}')
                        w.send(msg.encode())
                for err in r_errors:
                    logger.error(f'Handling exception for {err.getpeername()}')
                    self.potential_reads.remove(err)
                    if err in self.potential_writes:
                        self.potential_writes.remove(err)
                    err.close()
                    del self.queued_messages[err]

        except KeyboardInterrupt:
            print(f"\nServer interrupted, closing socket connections")
            self.close()

    def _clear_outbox(self, client_socket):
        if client_socket in self.queued_messages:
            self.queued_messages[client_socket] = str()

    def close(self):
        """
        Close all readable sockets
        (including server socket)
        """
        # self.server_socket.close() # might not need but faced problems without it
        for s in self.potential_reads:
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