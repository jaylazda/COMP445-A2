#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021
#
# Distributed under terms of the MIT license.

"""
Description:

"""
import socket
import select

import asyncio
import logging
import sys
import os


import patterns
import view
import argparse

logging.basicConfig(filename='view.log', level=logging.DEBUG)
logger = logging.getLogger()


class IRCClient(patterns.Subscriber):

    def __init__(self):
        super().__init__()
        self.username = str()
        self._run = True
        self.is_connected = False

    def __init__(self, nickname, host, port):
        super().__init__()
        self.nickname = nickname
        self.host = host
        self.port = port
        self._run = True
        self.is_connected = False

    def set_view(self, view):
        self.view = view

    def update(self, msg):
        # Will need to modify this
        if not isinstance(msg, str):
            raise TypeError(f"Update argument needs to be a string")
        elif not len(msg):
            # Empty string
            return
        logger.info(f"IRCClient.update -> msg: {msg}")
        self.process_input(msg)

    def process_input(self, msg):
        # Will need to modify this
        if msg.lower().startswith('/connect '):
            self.add_msg(msg)
            split_string = msg.split(" ")
            if len(split_string) > 4:
                self.username = split_string[1]
                self.server_host = split_string[2]
                self.server_port = split_string[3]
                self.real_name = split_string[4]
                self.connect()

        if msg.lower().startswith('/msg '):
            msg = msg[5:]
            self.add_msg(msg)
            self.send_message(msg)

        if msg.lower().startswith('/quit'):
            # Command that leads to the closure of the process
            raise KeyboardInterrupt

    def add_msg(self, msg):
        self.view.add_msg(self.nickname, msg)

    def add_msg_from_other_user(self, nickname, msg):
        self.view.add_msg(nickname, msg)

    async def run(self):
        """
        Driver of your IRC Client
        """
        try:
            while True:
                if hasattr(self, 'server_socket'):
                    socket_list = [sys.stdin, self.server_socket]
                    read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])
                    for sock in read_sockets:
                        # incoming message from remote server
                        if sock == self.server_socket:
                            data = sock.recv(4096).decode('utf-8')
                            if not data:
                                print('\nDisconnected from chat server')
                            else:
                                if data.startswith("NICK"):
                                    nickname = data.split(":")[0][5:]
                                    message = data[len(nickname)+6:]
                                    self.add_msg_from_other_user(nickname, message)
                                else:
                                    self.add_msg(data)
                        else:
                            pass
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            self.add_msg(f"\nServer interrupted, closing socket connections")
            self.close()
        except RuntimeError:
            self.add_msg(f"\nConnection interrupted, closing socket connections")
            self.close()

    def close(self):
        # Terminate connection
        logger.debug(f"Closing IRC Client object")
        pass

    def connect(self):
        if hasattr(self, 'nickname'):
            nick_msg = " ".join(["NICK", self.nickname])

        if hasattr(self, 'username') and hasattr(self, 'server_host') and hasattr(self, 'server_port'):
            user_msg = " ".join(["USER", self.username, self.server_host, self.server_port, self.real_name])

        if not(hasattr(self, 'server_socket')):
            self.connect_to_server()

        logger.info(f"Nick: {nick_msg} User: {user_msg}")
        msg = ";".join([nick_msg, user_msg])
        logger.info(f"Msg: {msg}")
        self.server_socket.send(msg.encode())
        logger.info("NICK USER sent")
        self.is_connected = True

    def send_message(self, msg):
        if self.is_connected:
            msg = "".join(["PRIVMSG #Global :", msg])
            logger.info(f"Sending message {msg} to server")
            logger.info(f"Server socket is {self.server_socket}")
            self.server_socket.send(msg.encode())

    def connect_to_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.info(f"connecting to socket at host:{self.server_host}:{self.server_port}")
        self.server_socket.connect((str(self.server_host), int(self.server_port)))
        logger.info(f"connected to server")


def set_parser(): 
    parser = argparse.ArgumentParser()
    parser.add_argument('--nickname', action="store", dest="nickname", default="client_01")
    parser.add_argument('--host', action="store", dest="host", default="localhost", help="server hostname")
    parser.add_argument('--port', action="store", dest="port", default=8081, help="server port number")
    return parser  

def main(args):
    # Pass your arguments where necessary
    client = IRCClient(args.nickname, args.host, args.port)
    logger.info(f"Client object created")
    with view.View() as v:
        logger.info(f"Entered the context of a View object")
        client.set_view(v)
        client.add_msg("Type /connect <username> <serverhost> <serverport> <realname> to connect to a server!")
        logger.debug(f"Passed View object to IRC Client")
        v.add_subscriber(client)
        logger.debug(f"IRC Client is subscribed to the View (to receive user input)")
        async def inner_run():
            await asyncio.gather(
                v.run(),
                client.run(),
                return_exceptions=True,
            )
        try:
            asyncio.run( inner_run() )
        except KeyboardInterrupt as e:
            logger.debug(f"Signifies end of process")
    client.close()

if __name__ == "__main__":
    parser = set_parser()
    args = parser.parse_args()

    main(args)
