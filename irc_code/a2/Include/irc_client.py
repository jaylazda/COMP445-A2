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
MSGLEN = 1000


class IRCClient(patterns.Subscriber):

    def __init__(self):
        super().__init__()
        self.username = str()
        self._run = True
        self.is_connected = False
        #create_client_socket(self)

    def __init__(self, nickname, host, port):
        super().__init__()
        self.nickname = nickname
        self.host = host
        self.port = port
        self._run = True
        self.is_connected = False
        #create_client_socket(self)

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
                connect(self)
                self.connect()

        if msg.lower().startswith('/msg '):
            self.add_msg(msg)
            split_string = msg.split('/msg ', 1)
            if len(split_string) == 2:
                send_message(self, msg)
                self.send_message(self, msg)

        if msg.lower().startswith('/quit'):
            # Command that leads to the closure of the process
            raise KeyboardInterrupt

    def add_msg(self, msg):
        self.view.add_msg(self.nickname, msg)

    async def run(self):
        """
        Driver of your IRC Client
        """
        try:
            while True:
                self.add_msg("here")
                if hasattr(self, 'server_socket'):
                    chunks = []
                    bytes_recd = 0
                    while bytes_recd < MSGLEN:
                        chunk = self.server_socket.recv(min(MSGLEN - bytes_recd, 2048))
                        if chunk == b'':
                            raise RuntimeError("socket connection broken")
                        chunks.append(chunk)
                        bytes_recd = bytes_recd + len(chunk)
                    message = b''.join(chunks)
                    self.add_msg(message)
                await asyncio.sleep(2)

        except KeyboardInterrupt:
            print(f"\nServer interrupted, closing socket connections")
            self.close()
        except RuntimeError:
            print(f"\Connection interrupted, closing socket connections")
            print(f"\nConnection interrupted, closing socket connections")
            self.close()

    def close(self):
        # Terminate connection
        logger.debug(f"Closing IRC Client object")
        pass

    def connect(self):
        if (hasattr(self, 'nickname')):
        if hasattr(self, 'nickname'):
            nick_msg = " ".join(["NICK", self.nickname])

        if hasattr(self, 'username') and hasattr(self, 'server_host') and hasattr(self, 'server_port'):
            user_msg = " ".join(["USER", self.username, self.server_host, self.server_port])

        if not(hasattr(self, 'server_socket')):
            create_server_socket(self)
            
        msg = ";".join(nick_msg, user_msg)
        self.server_socket.send(msg)
            self.connect_to_server()

        logger.info(f"Nick: {nick_msg} User: {user_msg}")
        msg = f"{nick_msg};{user_msg}"
        logger.info(f"Msg: {msg}")
        self.server_socket.send(msg.encode())
        logger.info("NICK USER sent")
        self.is_connected = True

    def send_message(self, msg):
        if self.is_connected:
            msg = " ".join(["PRIVMSG", msg])
            self.server_socket.send(msg)

    # def create_client_socket(self):
    #     self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     self.client_socket.setblocking(False) #server won't block at server_socket.accept()
    #     self.client_socket.bind((self.host, self.port))
    #     self.client_socket.listen()

    #     self.potential_reads = list()
    #     self.potential_reads.append(self.client_socket)
    #     self.potential_writes = list()
    #     self.potential_errors = list()

    def create_server_socket(self):
    def connect_to_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setblocking(False) #server won't block at server_socket.accept()
        self.server_socket.connect((self.server_host, self.server_port))
        self.potential_reads.append(self.server_socket)
        logger.info(f"connecting to socket at host:{self.server_host}:{self.server_port}")
        self.server_socket.connect((str(self.server_host), int(self.server_port)))
        logger.info(f"connected to server")


def set_parser(): 
    parser = argparse.ArgumentParser()
    parser.add_argument('--nickname', action="store", dest="nickname", default="client_01")
    parser.add_argument('--host', action="store", dest="host", default="localhost")
    parser.add_argument('--port', action="store", dest="port", default="1337")
    return parser  

def main(args):
    # Pass your arguments where necessary
    client = IRCClient(args.nickname, args.host, args.port)
    logger.info(f"Client object created")
    with view.View() as v:
        logger.info(f"Entered the context of a View object")
        client.set_view(v)
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
