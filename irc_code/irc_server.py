"""
SERVER
"""
import socket
import select

class Server:

    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setblocking(False) #server won't block at server_socket.accept()
        host, port = 'localhost', 8081
        self.server_socket.bind((host, port))
        self.server_socket.listen()

        #Select vars
        self.potential_reads = list()
        self.potential_reads.append(self.server_socket)
        self.potential_writes = list()
        self.potential_errors = list()
        self.outbox = dict()
        self.messages = dict()
        self.read_size = 2**10

    def run(self):
        print("Running server at localhost:8081")
        try:
            while True:
                r_reads, r_writes, r_errors = select.select(self.potential_reads, self.potential_writes, self.potential_errors)
                for r in r_reads:
                    # Server socket accepting clients
                    if r is self.server_socket:
                        client_socket, addr = r.accept()
                        client_socket.setblocking(False)
                        print("New client @ {}".format(addr))
                        msg = "Hello client"
                        self.outbox[client_socket] = "HTTP/1.0 200 OK\r\nContent-Length: {}\r\n\r\n{}".format(len(msg), msg)
                        self.messages[client_socket] = str()
                        self.potential_reads.append(client_socket)
                        self.potential_writes.append(client_socket)
                    # Reading from clients
                    else:
                        data = r.recv(self.read_size).decode('utf-8')
                        if data:
                            print(f"Received data: {data}")
                            self.messages[r] += data
                            self._parse_message(r)
                            pass
                        # Data is empty
                        else:
                            self.potential_reads.remove(r)
                            self.potential_writes.remove(r)
                            if r is self.outbox:
                                del self.outbox[r]
                            if r is self.messages:
                                del self.messages[r]
                            print(f"Closed a client socket: {r}")
                            r.close()
                for w in r_writes:
                    msg = self.outbox[w]
                    if len(msg):
                        w.send(msg.encode()) # String to bytes
                        self._clear_outbox(w)
                for err in r_errors:
                    self.potential_reads.remove(err)
                    if err is self.outbox:
                        del self.outbox[err]
                    if err is self.messages:
                        del self.messages[err]

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
        for s in self.potential_reads:
            s.close()

    def _parse_message(self, client):
        """
        If message is bigger than the read size then it must be broken up
        """
        pass

if __name__ == "__main__":
    server = Server()
    server.run()