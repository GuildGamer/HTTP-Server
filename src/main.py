import os
import socket
import mimetypes


class TCPServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8088):
        self.host = host
        self.port = port

    def start(self):
        # creating a socket instance specifying the address family and the socket type
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind the socket to the host and port specified
        s.bind((self.host, self.port))

        # listen tells the socket library that we want it to queue up as many as 5 connect requests (the normal max) before refusing outside connections
        s.listen(5)

        print("Listening for requests at ", s.getsockname())

        # This means that the server keeps listening whithout end
        while True:
            # Allows socket accept new connections
            connection, address = s.accept()

            print("Connected to by", address)

            # read the first 1024 bytes of the data sent by the client
            data = connection.recv(1024)

            response = self.handle_request(data)

            # send back the data to the client
            connection.sendall(response)

            # close the connection
            connection.close()

    # This handles requests
    def handle_request(self, data):
        return data


class HTTPServer(TCPServer):
    headers = {
        "Server": "CrudeServer",
        "Content-Type": "text/html",
    }

    status_codes = {
        200: "OK",
        404: "Not Found",
        501: "Not Implemented",
    }

    def handle_request(self, data):
        # This created an instance of HTTPRequest and parses the request to get the attribute values
        request = HTTPRequest(data)

        # This dynamically gets the function to use to handle the request based on the request method
        try:
            handler = getattr(self, "handle_%s" % request.method)
        except AttributeError:
            # Throw an exception if the the appropriate request handler is not found
            handler = self.HTTP_501_handler

        response = handler(request)

        return response

    def handle_GET(self, request):
        filename = request.uri.strip("/")

        if os.path.exists("../static/" + filename):
            response_line = self.response_line(status_code=200)

            # find out a file's MIME type so we can serve media files as well
            # if nothing is found, just send `text/html`
            content_type = mimetypes.guess_type(filename)[0] or "text/html"

            extra_headers = {"Content-Type": content_type}

            # We set extra headers for our response
            response_headers = self.response_headers(extra_headers)

            with open("../static/" + filename, "rb") as f:
                response_body = f.read()

        else:
            response_line = self.response_line(status_code=404)
            response_headers = self.response_headers()
            response_body = b"<h1>404 Not Found</h1>"

        blank_line = b"\r\n"

        # This are the contents of a HTTP response
        return b"".join([response_line, response_headers, blank_line, response_body])

    def HTTP_501_handler(self, request):
        response_line = self.response_line(status_code=501)

        response_headers = self.response_headers()

        blank_line = b"\r\n"

        response_body = b"<h1>501 Not Implemented</h1>"

        return b"".join([response_line, response_headers, blank_line, response_body])

    def response_line(self, status_code):
        """Returns response line"""
        reason = self.status_codes[status_code]
        line = "HTTP/1.1 %s %s\r\n" % (status_code, reason)

        return line.encode()  # call encode to convert str to bytes

    def response_headers(self, extra_headers=None):
        """Returns headers
        The `extra_headers` can be a dict for sending
        extra headers for the current response
        """
        headers_copy = self.headers.copy()  # make a local copy of headers

        if extra_headers:
            headers_copy.update(extra_headers)

        headers = ""

        for h in headers_copy:
            headers += "%s: %s\r\n" % (h, headers_copy[h])

        return headers.encode()


class HTTPRequest:
    def __init__(self, data):
        self.method = None
        self.uri = None
        self.http_version = "1.1"

        self.parse(data)

    def parse(self, data):
        # We use the line break as a delimiter because we know that every part of a HTTP request ends with the line break character
        lines = data.split(b"\r\n")

        request_line = lines[0]

        words = request_line.split(b" ")

        self.method = words[0].decode()  # call decode to convert bytes to str

        if len(words) > 1:
            # we put this in an if-block because sometimes
            # browsers don't send uri for homepage
            self.uri = words[1].decode()  # call decode to convert bytes to str

        if len(words) > 2:
            self.http_version = words[2]


if __name__ == "__main__":
    server = HTTPServer()
    server.start()
