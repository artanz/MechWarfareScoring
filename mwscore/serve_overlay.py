#!/usr/bin/env python3
"""
Serves the OBS overlay and score data over HTTP for use in OBS Browser Source.

Usage:
    python3 serve_overlay.py

Then add an OBS Browser Source pointing to:
    http://localhost:8080/obs_overlay.html
"""
import http.server
import functools

PORT = 8080

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=".")
server = http.server.HTTPServer(("", PORT), handler)

print("Serving OBS overlay at http://localhost:%d/obs_overlay.html" % PORT)
print("Press Ctrl+C to stop.")
try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nStopped.")
    server.server_close()
