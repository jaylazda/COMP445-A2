Pierre-Anthony and Jacob Lazda

USAGE OF THE APPLICATION

-The application must be run using the provided venv.

-irc_server.py
-The server can be run in the provided venv with no provided --port command, as it will default to 8081.

-irc_client.py
-The client can be provided with the following 3 optional arguments:
--nickname to label the client (default is client_01)
--host to label the server host (default is localhost)
--port to specify the server port (default is port 8081)
-Note that only the nickname needs to be provided to test the usage of multiple clients.

In the client, the following commands can be used:

/connect <username> <server hostname> <server port> <realname> will attempt to connect the client to the server
and add them to the #Global channel. If another user on the channel has the same username, the new user will not 
join the channel and will need to connect with a different username.

/msg <message here> will send a message to all the clients on the channel if the client is connected to the #Global channel.

/quit lets the user quit and deregister from the #Global channel