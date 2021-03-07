Pierre-Anthony and Jacob Lazda

USAGE OF THE APPLICATION

-The application must be ran using the provided venv. 

-irc_server.py
  -The server can be ran in the provided venv with no provided --port command, as it will default to 8081.

-irc_client.py
  -The client can be provided with every necessary argument
    --nickname to label the client
    --host to label the server host
    --port to specify the server port
    --username to specify the username
    --realname to specify the real name of the user
  -Note that only the nickname and the username need to be provided to test the usage of multiple clients.
  -In the client, the following commands can be used
     /connect will automatically connect to the server
     /msg <message_here> will send a message to the server if the client has been connected to the server.