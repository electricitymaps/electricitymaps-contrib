#! /usr/bin/env python

# Usage: python __file__.py <port>

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler, test
from urllib.parse import urlparse


def get_country_code_from_query_string(path):
    query = urlparse(path).query
    query_dict = dict(qc.split("=") for qc in query.split("&"))
    return query_dict.get("countryCode", None)


class MockServer(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, "OK")
        self.end_headers()

    def do_GET(self):
        if "/v3/history" in self.path and "countryCode" in self.path:
            country_code = get_country_code_from_query_string(self.path)
            filename = (
                f"v3/history_{country_code}"
                if os.path.isfile(f"v3/history_{country_code}")
                else "v3/history"
            )
            with open(filename, "r") as f:
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(json.load(f)).encode("utf-8"))
        else:
            SimpleHTTPRequestHandler.do_GET(self)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Headers",
            "x-request-timestamp, x-signature, electricitymap-token",
        )
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        SimpleHTTPRequestHandler.end_headers(self)


if __name__ == "__main__":
    test(MockServer, HTTPServer)
