#! /usr/bin/env python

# Usage: python __file__.py <port>

from http.server import SimpleHTTPRequestHandler, HTTPServer, test

class CORSRequest(SimpleHTTPRequestHandler):
    def doop(self):
        self.send_response(200, 'OK')
        self.end_headers()

    def endheaders(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'x-request-timestamp, x-signature, electricitymap-token')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        SimpleHTTPRequestHandler.end_headers(self)

if __name__ == '__main__':
    test(CORSRequest, HTTPServer)
