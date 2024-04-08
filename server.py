import os
import http.server
import socketserver

from http import HTTPStatus


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        script_name = self.path.strip('/')
        if script_name.endswith('.py'):
            try:
                module = __import__(script_name[:-3])
                module.main(self)
            except ImportError:
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()
                self.wfile.write(b'404 - Not Found')
        else:
            super().do_GET()


port = int(os.getenv('PORT', 80))
print('Listening on port %s' % (port))
httpd = socketserver.TCPServer(('', port), CustomHandler)
httpd.serve_forever()
