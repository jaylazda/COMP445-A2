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

from threading import Thread

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

    def __init__(self, nickname, server_host, server_port, username, realname):
        super().__init__()
        self.nickname = nickname
        self.server_host = server_host
        self.server_port = server_port
        self.username = username
        self.realname = realname
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
        if msg.lower().startswith('/connect'):
            self.add_msg(msg)
            self.connect()

        if msg.lower().startswith('/msg '):
            self.add_msg(msg)
            split_string = msg.split('/msg ', 1)
            if len(split_string) == 2:
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
                    self.add_msg("awaiting")
                    data = self.server_socket.recv(4096)
                    self.add_msg("got it")
                    if not data :
                        print ('Disconnected from chat server')
                    self.add_msg(data)
                await asyncio.sleep(2)
        except KeyboardInterrupt:
            self.add_msg(f"\nServer interrupted, closing socket connections")
            self.close()
        except RuntimeError:
            self.add_msg(f"\nConnection interrupted, closing socket connections")
            self.close()
        except Exception as e:
            self.add_msg("<p>Error: %s</p>" % str(e) ) 

    def close(self):
        # Terminate connection
        logger.debug(f"Closing IRC Client object")
        pass

    def connect(self):
        if hasattr(self, 'nickname'):
            nick_msg = " ".join(["NICK", self.nickname])

        if hasattr(self, 'username') and hasattr(self, 'server_host') and hasattr(self, 'server_port'):
            user_msg = " ".join(["USER", self.username, self.server_host, self.server_port, self.realname])

        if not(hasattr(self, 'server_socket')):
            self.connect_to_server()

        logger.info(f"Nick: {nick_msg} User: {user_msg}")
        msg = f"{nick_msg};{user_msg}"
        logger.info(f"Msg: {msg}")
        self.server_socket.send(msg.encode())
        logger.info("NICK USER sent")
        self.is_connected = True

    def send_message(self, msg):
        if self.is_connected:
            msg = " ".join(["PRVMSG", msg])
            self.server_socket.send(msg.encode())

    # def create_client_socket(self):
    #     self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     self.client_socket.setblocking(False) #server won't block at server_socket.accept()
    #     self.client_socket.bind((self.host, self.port))
    #     self.client_socket.listen()

    #     self.potential_reads = list()
    #     self.potential_reads.append(self.client_socket)
    #     self.potential_writes = list()
    #     self.potential_errors = list()

    def connect_to_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.info(f"connecting to socket at host:{self.server_host}:{self.server_port}")
        self.server_socket.connect((str(self.server_host), int(self.server_port)))
        logger.info(f"connected to server")


def set_parser(): 
    parser = argparse.ArgumentParser()
    parser.add_argument('--nickname', action="store", dest="nickname", default="client_01")
    parser.add_argument('--host', action="store", dest="server_host", default="localhost")
    parser.add_argument('--port', action="store", dest="server_port", default="8081")
    parser.add_argument('--username', action="store", dest="username", default="xxN00bDestroyerxx")
    parser.add_argument('--realname', action="store", dest="realname", default="Joe Tremblay")
    return parser  

def main(args):
    # Pass your arguments where necessary
    client = IRCClient(args.nickname, args.server_host, args.server_port, args.username, args.realname)
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
