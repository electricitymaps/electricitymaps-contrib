#! /usr/bin/env python

# Usage: python __file__.py <port>

from http.server import SimpleHTTPRequestHandler, HTTPServer, test

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, 'OK')
        self.end_headers()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'x-request-timestamp, x-signature, electricitymap-token')
        SimpleHTTPRequestHandler.end_headers(self)

if __name__ == '__main__':
    test(CORSRequestHandler, HTTPServer)
